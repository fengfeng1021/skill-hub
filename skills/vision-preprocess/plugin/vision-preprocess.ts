import { appendFile, mkdir, readFile } from "node:fs/promises"
import { Buffer } from "node:buffer"
import { homedir as osHomedir, tmpdir } from "node:os"
import { join } from "node:path"
import type { Plugin } from "@opencode-ai/plugin"

const ZEN_ENDPOINT = "https://opencode.ai/zen/v1/chat/completions"
const MIMO_MODEL = process.env.OPENCODE_VISION_MIMO_MODEL || "mimo-v2.5-free"
const MAX_TOKENS = 2048
const REQUEST_TIMEOUT_MS = 30_000

const LITE_MODELS = [
  "gemini-3.5-flash-lite",
  "gemini-3.1-flash-lite",
  "gemini-3.1-flash-lite-preview",
]

function homedir(): string {
  return process.env.USERPROFILE || process.env.HOME || osHomedir()
}

async function loadGeminiAuth(): Promise<{ base: string; key: string }> {
  const base =
    process.env.OPENCODE_VISION_GEMINI_BASE || "https://aiapi.tw/v1beta"
  let key = process.env.OPENCODE_VISION_GEMINI_KEY || ""
  if (!key) {
    try {
      const cfg = JSON.parse(
        await readFile(join(homedir(), ".config", "opencode", "opencode.json"), "utf8")
      )
      key = cfg.provider?.gemini?.options?.apiKey || ""
    } catch {
      // ignore
    }
  }
  return { base, key }
}

async function loadZenKey(): Promise<string> {
  try {
    const auth = JSON.parse(
      await readFile(join(homedir(), ".local", "share", "opencode", "auth.json"), "utf8")
    )
    return auth["opencode-go"]?.key || ""
  } catch {
    return ""
  }
}

const cache = new Map<string, string>()

function cacheKey(sessionID: string, messageID: string, partID: string): string {
  return `${sessionID}:${messageID}:${partID}`
}

const IMAGE_EXT_RE = /\.(png|jpe?g|gif|webp|bmp|avif|heic|svg)$/i

function isImagePart(p: any): boolean {
  if (p.type !== "file") return false
  if (p.mime && p.mime.startsWith("image/")) return true
  const name = String(p.filename || p.url || "").toLowerCase()
  if (name.startsWith("data:image/")) return true
  return IMAGE_EXT_RE.test(name)
}

async function logDebug(line: string): Promise<void> {
  try {
    const directory = join(process.env.TEMP || tmpdir(), "opencode")
    await mkdir(directory, { recursive: true })
    await appendFile(join(directory, "vision-debug.log"), `${new Date().toISOString()} ${line}\n`, "utf8")
  } catch {
    // ignore
  }
}

const VISION_PROMPT =
  "你是視覺分析模型。請詳盡描述這張圖片：1) 畫面內容與主體；2) 所有可見文字（完整 OCR）；3) UI 佈局與元素；4) 明顯的錯誤或異常；5) 與使用者可能問題相關的細節。以繁體中文回覆。"

async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const ac = new AbortController()
  const timer = setTimeout(() => ac.abort(), timeoutMs)
  try {
    return await fetch(url, { ...init, signal: ac.signal })
  } finally {
    clearTimeout(timer)
  }
}

async function bytesToDataUrl(data: ArrayBuffer | Buffer | string, mime: string): Promise<string> {
  if (typeof data === "string") {
    if (data.startsWith("data:")) return data
    if (data.startsWith("http://") || data.startsWith("https://")) {
      const res = await fetch(data)
      const buf = await res.arrayBuffer()
      return `data:${mime};base64,${Buffer.from(buf).toString("base64")}`
    }
    const buf = await readFile(data)
    return `data:${mime};base64,${buf.toString("base64")}`
  }
  return `data:${mime};base64,${Buffer.from(data).toString("base64")}`
}

function parseDataUrl(dataUrl: string): { mime: string; data: string } {
  const m = /^data:([^;,]+);base64,(.+)$/.exec(dataUrl)
  if (!m) throw new Error("invalid data url")
  return { mime: m[1], data: m[2] }
}

async function describeWithGemini(
  dataUrl: string,
  base: string,
  key: string,
  model: string
): Promise<string> {
  const { mime, data } = parseDataUrl(dataUrl)
  const res = await fetchWithTimeout(
    `${base.replace(/\/$/, "")}/models/${model}:generateContent`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-goog-api-key": key },
      body: JSON.stringify({
        contents: [
          {
            role: "user",
            parts: [{ text: VISION_PROMPT }, { inline_data: { mime_type: mime, data } }],
          },
        ],
        generationConfig: { maxOutputTokens: MAX_TOKENS },
      }),
    },
    REQUEST_TIMEOUT_MS
  )
  const json = await res.json()
  if (!res.ok) throw new Error(`${res.status} ${JSON.stringify(json.error || json).slice(0, 200)}`)
  const text = json.candidates?.[0]?.content?.parts
    ?.map((p: any) => p.text || "")
    .join("")
    .trim()
  if (!text) throw new Error("empty gemini response")
  return text
}

async function describeWithMimo(dataUrl: string, key: string): Promise<string> {
  const res = await fetchWithTimeout(
    ZEN_ENDPOINT,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
      body: JSON.stringify({
        model: MIMO_MODEL,
        max_tokens: MAX_TOKENS,
        messages: [
          {
            role: "user",
            content: [
              { type: "text", text: VISION_PROMPT },
              { type: "image_url", image_url: { url: dataUrl } },
            ],
          },
        ],
      }),
    },
    REQUEST_TIMEOUT_MS
  )
  const json = await res.json()
  if (!res.ok) throw new Error(`${res.status} ${JSON.stringify(json.error || json).slice(0, 200)}`)
  const content = json.choices?.[0]?.message?.content
  if (!content) throw new Error("empty mimo response")
  return String(content)
}

export default (async () => {
  const { base, key } = await loadGeminiAuth()
  const zenKey = await loadZenKey()

  return {
    "experimental.chat.messages.transform": async (input, output) => {
      await logDebug(`HOOK messages=${output.messages.length} geminiKey=${Boolean(key)} zenKey=${Boolean(zenKey)}`)
      if (!key && !zenKey) return

      for (const message of output.messages) {
        await logDebug(
          `TRANSFORM messages=${output.messages.length} info=${message.info?.role ?? "?"} parts=${message.parts?.length ?? 0} types=${JSON.stringify((message.parts ?? []).map((p: any) => p.type))}`
        )
        if (!message.parts?.length) continue

        for (const p of message.parts) {
          await logDebug(
            `  PART type=${p.type} mime=${JSON.stringify(p.mime)} filename=${JSON.stringify(p.filename)} urlHead=${String((p as any).url || "").slice(0, 60)} keys=${JSON.stringify(Object.keys(p))}`
          )
        }

        const images = message.parts.filter(isImagePart)
        if (!images.length) continue

        const replacements: { part: any; text: string }[] = []

        for (const img of images) {
          const ck = cacheKey(img.sessionID, img.messageID, img.id)
          const cached = cache.get(ck)
          if (cached) {
            replacements.push({ part: img, text: cached })
            continue
          }

          let dataUrl: string | null = null
          try {
            const raw = img.url ?? ""
            if (!raw) throw new Error("image part has no url")
            dataUrl = await bytesToDataUrl(raw, img.mime)
          } catch (e) {
            const msg = `[使用者貼了一張圖片，但視覺預處理失敗（${(e as Error).message}）。如需分析可用 /agent vision 手動處理]`
            replacements.push({ part: img, text: msg })
            continue
          }

          let desc = ""
          let usedModel = ""
          let lastErr: Error | null = null

          if (key) {
            for (const model of LITE_MODELS) {
              if (desc) break
              try {
                desc = await describeWithGemini(dataUrl, base, key, model)
                usedModel = `gemini/${model}`
                break
              } catch (e) {
                lastErr = e as Error
              }
            }
          }

          if (!desc && zenKey) {
            try {
              desc = await describeWithMimo(dataUrl, zenKey)
              usedModel = `opencode/${MIMO_MODEL}`
            } catch (e) {
              lastErr = e as Error
            }
          }

          if (desc) {
            const text = `[使用者貼了一張圖片，已由視覺模型 ${usedModel} 自動預處理]\n${desc}`
            cache.set(ck, text)
            replacements.push({ part: img, text })
          } else {
            const msg = `[使用者貼了一張圖片，但視覺預處理失敗（${lastErr ? lastErr.message : "無可用視覺模型"}）。如需分析可用 /agent vision 手動處理]`
            replacements.push({ part: img, text: msg })
          }
        }

        for (const { part, text } of replacements) {
          const idx = message.parts.indexOf(part)
          if (idx === -1) continue
          message.parts.splice(idx, 1, {
            id: `vis-${Math.random().toString(36).slice(2, 10)}`,
            sessionID: part.sessionID,
            messageID: part.messageID,
            type: "text",
            text,
            synthetic: true,
          })
        }
      }
    },

    "experimental.chat.system.transform": async (input, output) => {
      output.system.push(
        "使用者貼上的圖片會被自動交給視覺模型預處理，以 [使用者貼了一張圖片，已由視覺模型...] 開頭的文字形式呈現，請直接視為圖片內容使用。"
      )
    },
  }
}) satisfies Plugin
