"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Bot,
  Loader2,
  MessageCircle,
  MessageCirclePlus,
  Send,
  Trash2,
  UserRound,
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import rehypeKatex from "rehype-katex"
import remarkMath from "remark-math"
import { memo, useEffect, useRef, useState, useSyncExternalStore } from "react"
import type { FormEvent } from "react"

import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import {
  apiDelete,
  apiGet,
  apiStreamPost,
  errorMessage,
  type ChatVisualization,
} from "@/lib/api"
import { formatDate, formatKwh, formatNumber, formatVnd } from "@/lib/format"

interface Conversation {
  id: string
  user_id: number
  title: string
  created_at: string
  updated_at: string
}
interface Message {
  id: string
  role: "user" | "model"
  content: string
  created_at: string
  visualization?: ChatVisualization | null
}
interface ConversationDetail extends Conversation {
  messages: Message[]
}

function subscribeToConversationUrl(onChange: () => void) {
  window.addEventListener("popstate", onChange)
  window.addEventListener("conversation-url-change", onChange)
  return () => {
    window.removeEventListener("popstate", onChange)
    window.removeEventListener("conversation-url-change", onChange)
  }
}

function getConversationIdFromUrl() {
  return new URLSearchParams(window.location.search).get("conversation_id")
}

function updateConversationUrl(id?: string) {
  const url = new URL(window.location.href)
  if (id) url.searchParams.set("conversation_id", id)
  else url.searchParams.delete("conversation_id")
  window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`)
  window.dispatchEvent(new Event("conversation-url-change"))
}

const SUGGESTIONS = [
  "Tháng này tiêu thụ bao nhiêu kWh?",
  "So sánh tiêu thụ tháng này với tháng trước",
  "Tầng nào tiêu thụ điện nhiều nhất trong 30 ngày qua?",
]

const assistantMessageClass =
  "max-w-[85%] rounded-xl bg-muted px-4 py-3 text-sm " +
  "[&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 " +
  "[&_p]:my-2 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0 " +
  "[&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-1 [&_strong]:font-semibold " +
  "[&_h1]:mb-2 [&_h1]:mt-3 [&_h1]:text-lg [&_h1]:font-semibold " +
  "[&_h2]:mb-2 [&_h2]:mt-3 [&_h2]:text-base [&_h2]:font-semibold " +
  "[&_h3]:mb-2 [&_h3]:mt-3 [&_h3]:font-semibold " +
  "[&_blockquote]:my-2 [&_blockquote]:border-l-2 [&_blockquote]:pl-3 " +
  "[&_blockquote]:text-muted-foreground [&_code]:rounded [&_code]:bg-background/70 " +
  "[&_code]:px-1 [&_code]:py-0.5 [&_pre]:my-2 [&_pre]:overflow-x-auto " +
  "[&_pre]:rounded [&_pre]:bg-background/70 [&_pre]:p-3"

const markdownRemarkPlugins = [remarkMath]
const markdownRehypePlugins = [rehypeKatex]

const AssistantMessage = memo(function AssistantMessage({ content }: { content: string }) {
  return (
    <div className={assistantMessageClass}>
      <ReactMarkdown remarkPlugins={markdownRemarkPlugins} rehypePlugins={markdownRehypePlugins}>
        {content}
      </ReactMarkdown>
    </div>
  )
})

function AnalyticsTable({
  title,
  description,
  headers,
  rows,
}: {
  title: string
  description: string
  headers: string[]
  rows: string[][]
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="max-h-80 overflow-auto rounded-md border">
          <Table>
            <TableHeader className="sticky top-0 bg-muted/50">
              <TableRow>
                {headers.map((header) => (
                  <TableHead key={header}>{header}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody className="tabular-nums">
              {rows.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <TableCell key={cellIndex}>{cell}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}

const AnalyticsVisualization = memo(function AnalyticsVisualization({
  data,
}: {
  data: ChatVisualization
}) {
  const floors = data.floors?.items ?? []
  const rooms = data.rooms?.items ?? []
  const hourly = data.hourly?.items ?? []
  const summary = data.summary
  const hasContent = Boolean(summary || floors.length || rooms.length || hourly.length)

  if (!hasContent) return null

  const period =
    summary?.from_date && summary.to_date
      ? `${formatDate(summary.from_date)} – ${formatDate(summary.to_date)}`
      : undefined
  return (
    <section className="w-full space-y-4" aria-label="Phân tích dữ liệu năng lượng">
      {summary ? (
        <AnalyticsTable
          title="Tổng quan tiêu thụ"
          description="Số liệu lấy trực tiếp từ công cụ phân tích"
          headers={["Chỉ số", "Giá trị"]}
          rows={[
            ...(period ? [["Kỳ thống kê", period]] : []),
            ["Tổng điện năng", formatKwh(summary.total_kwh)],
            ["Tổng chi phí", formatVnd(summary.total_cost)],
          ]}
        />
      ) : null}

      <div className="space-y-4">
        {floors.length ? (
          <AnalyticsTable
            title="Tiêu thụ theo tầng"
            description="Điện năng, chi phí và tỷ trọng theo tầng"
            headers={["Tầng", "Điện năng", "Chi phí", "Tỷ trọng"]}
            rows={floors.map((floor) => [
              floor.floor_name || `Tầng ${floor.floor_number}`,
              formatKwh(floor.kwh),
              formatVnd(floor.cost),
              `${formatNumber(floor.share_percent, 1)}%`,
            ])}
          />
        ) : null}

        {rooms.length ? (
          <AnalyticsTable
            title="Phòng tiêu thụ nhiều nhất"
            description="Xếp hạng theo điện năng tiêu thụ"
            headers={["Phòng", "Tầng", "Điện năng", "Chi phí", "Tỷ trọng"]}
            rows={rooms.map((room) => [
              `${room.room_name} (${room.room_code})`,
              room.floor_name,
              formatKwh(room.kwh),
              formatVnd(room.cost),
              `${formatNumber(room.share_percent, 1)}%`,
            ])}
          />
        ) : null}

        {hourly.length ? (
          <AnalyticsTable
            title="Mức tiêu thụ trung bình theo giờ"
            description="So sánh ngày thường và cuối tuần"
            headers={["Giờ", "Ngày thường", "Cuối tuần"]}
            rows={hourly.map((item) => [
              `${String(item.hour).padStart(2, "0")}h`,
              formatKwh(item.weekday_kwh),
              formatKwh(item.weekend_kwh),
            ])}
          />
        ) : null}
      </div>
    </section>
  )
})

export function ChatView() {
  const queryClient = useQueryClient()
  const [conversationId, setConversationId] = useState<string>()
  const [isDraft, setIsDraft] = useState(false)
  const urlConversationId = useSyncExternalStore(
    subscribeToConversationUrl,
    getConversationIdFromUrl,
    () => null,
  )
  const [input, setInput] = useState("")
  const [pendingQuestion, setPendingQuestion] = useState<string>()
  const [streamedAnswer, setStreamedAnswer] = useState("")
  const [streamedVisualization, setStreamedVisualization] = useState<ChatVisualization>()
  const [streamComplete, setStreamComplete] = useState(false)
  const [streamStatus, setStreamStatus] = useState("")
  const [sendError, setSendError] = useState<string>()
  const endOfMessages = useRef<HTMLDivElement>(null)
  const pendingStreamChunks = useRef("")
  const streamFlushTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const streamDrainResolvers = useRef<Array<() => void>>([])

  function flushStreamedAnswer() {
    if (streamFlushTimeout.current !== null) {
      clearTimeout(streamFlushTimeout.current)
      streamFlushTimeout.current = null
    }
    const characters = Array.from(pendingStreamChunks.current)
    const chunk = characters.slice(0, 1).join("")
    pendingStreamChunks.current = characters.slice(1).join("")
    if (chunk) setStreamedAnswer((previous) => previous + chunk)
    if (pendingStreamChunks.current) {
      streamFlushTimeout.current = setTimeout(flushStreamedAnswer, 4)
      return
    }
    streamDrainResolvers.current.splice(0).forEach((resolve) => resolve())
  }

  function queueStreamedChunk(chunk: string) {
    pendingStreamChunks.current += chunk
    if (streamFlushTimeout.current !== null) return
    streamFlushTimeout.current = setTimeout(flushStreamedAnswer, 4)
  }

  function clearPendingStreamChunks() {
    if (streamFlushTimeout.current !== null) {
      clearTimeout(streamFlushTimeout.current)
      streamFlushTimeout.current = null
    }
    pendingStreamChunks.current = ""
    streamDrainResolvers.current.splice(0).forEach((resolve) => resolve())
  }

  function waitForStreamFlush() {
    if (!pendingStreamChunks.current && streamFlushTimeout.current === null) {
      return Promise.resolve()
    }
    return new Promise<void>((resolve) => {
      streamDrainResolvers.current.push(resolve)
    })
  }

  const conversations = useQuery({
    queryKey: ["chat", "conversations"],
    queryFn: () => apiGet<Conversation[]>("/chat/conversations"),
  })

  useEffect(() => {
    if (
      urlConversationId &&
      conversations.data &&
      !conversations.data.some((item) => item.id === urlConversationId)
    ) {
      updateConversationUrl()
    }
  }, [conversations.data, urlConversationId])

  const urlSelectedConversationId = conversations.data?.find(
    (item) => item.id === urlConversationId,
  )?.id
  const activeConversationId = isDraft
    ? undefined
    : conversationId ??
      (urlConversationId && !conversations.data
        ? undefined
        : urlSelectedConversationId ?? conversations.data?.[0]?.id)
  const conversation = useQuery({
    queryKey: ["chat", "conversation", activeConversationId],
    queryFn: () => apiGet<ConversationDetail>(`/chat/conversations/${activeConversationId}`),
    enabled: Boolean(activeConversationId),
  })
  const sendMessage = useMutation({
    mutationFn: async ({ content }: { content: string }) => {
      const result = await apiStreamPost(
        "/chat/messages",
        { conversation_id: activeConversationId ?? null, content },
        (chunk) => {
          setStreamStatus("")
          queueStreamedChunk(chunk)
        },
        setStreamedVisualization,
        setStreamStatus,
      )
      await waitForStreamFlush()
      return result
    },
    onSuccess: async ({ conversation_id }) => {
      setConversationId(conversation_id)
      updateConversationUrl(conversation_id)
      setIsDraft(false)
      setStreamComplete(true)
      setSendError(undefined)
      setStreamStatus("")
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] }),
        queryClient.invalidateQueries({ queryKey: ["chat", "conversation", conversation_id] }),
      ])
    },
    onError: (error) => {
      clearPendingStreamChunks()
      setPendingQuestion(undefined)
      setStreamedAnswer("")
      setStreamedVisualization(undefined)
      setStreamComplete(false)
      setStreamStatus("")
      setSendError(errorMessage(error))
    },
  })
  const deleteConversation = useMutation({
    mutationFn: (id: string) => apiDelete(`/chat/conversations/${id}`),
    onSuccess: async (_, deletedId) => {
      const remaining = conversations.data?.filter((item) => item.id !== deletedId) ?? []
      setConversationId(
        deletedId === activeConversationId ? remaining[0]?.id : conversationId,
      )
      if (deletedId === activeConversationId) {
        setIsDraft(false)
        updateConversationUrl(remaining[0]?.id)
      }
      await queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] })
      queryClient.removeQueries({ queryKey: ["chat", "conversation", deletedId] })
    },
  })

  useEffect(() => {
    endOfMessages.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [conversation.data, pendingQuestion, sendError, sendMessage.isPending])

  useEffect(() => {
    if (streamedAnswer) {
      endOfMessages.current?.scrollIntoView({ behavior: "auto", block: "end" })
    }
  }, [streamedAnswer])

  useEffect(
    () => () => {
      if (streamFlushTimeout.current !== null) {
        clearTimeout(streamFlushTimeout.current)
        streamFlushTimeout.current = null
      }
      pendingStreamChunks.current = ""
      streamDrainResolvers.current.splice(0).forEach((resolve) => resolve())
    },
    [],
  )

  function submitMessage(event: FormEvent<HTMLFormElement>, suggested?: string) {
    event.preventDefault()
    const content = (suggested ?? input).trim()
    if (!content || sendMessage.isPending) return
    clearPendingStreamChunks()
    setPendingQuestion(content)
    setStreamedAnswer("")
    setStreamedVisualization(undefined)
    setStreamComplete(false)
    setStreamStatus("Đang kết nối trợ lý…")
    setSendError(undefined)
    setInput("")
    sendMessage.mutate({ content })
  }

  function sendSuggested(question: string) {
    if (sendMessage.isPending) return
    clearPendingStreamChunks()
    setPendingQuestion(question)
    setStreamedAnswer("")
    setStreamedVisualization(undefined)
    setStreamComplete(false)
    setStreamStatus("Đang kết nối trợ lý…")
    setSendError(undefined)
    sendMessage.mutate({ content: question })
  }

  function startNewConversation() {
    clearPendingStreamChunks()
    setConversationId(undefined)
    updateConversationUrl()
    setIsDraft(true)
    setPendingQuestion(undefined)
    setStreamedAnswer("")
    setStreamedVisualization(undefined)
    setStreamComplete(false)
    setStreamStatus("")
    setSendError(undefined)
  }

  const messages = conversation.data?.messages ?? []
  const isSending = sendMessage.isPending
  const hasPersistedPendingTurn = Boolean(
    pendingQuestion &&
      streamedAnswer &&
      messages.some(
        (message, index) =>
          message.role === "user" &&
          message.content === pendingQuestion &&
          messages[index + 1]?.role === "model" &&
          messages[index + 1]?.content === streamedAnswer,
      ),
  )
  const showPendingTurn = Boolean(pendingQuestion && !hasPersistedPendingTurn)

  return (
    <div className="-mr-4 flex h-[calc(100dvh-5.5rem)] min-h-0 min-w-0 flex-col gap-4 overflow-hidden md:-mr-6 md:h-[calc(100dvh-6.5rem)]">
      <PageHeader
        title="Trợ lý AI"
        description="Hỏi về điện năng tiêu thụ, chi phí và xu hướng trong hệ thống"
      />

      <div className="grid min-h-0 min-w-0 flex-1 grid-rows-[auto_minmax(0,1fr)] gap-4 lg:grid-cols-[16rem_minmax(0,1fr)] lg:grid-rows-1">
        <Card className="flex max-h-44 min-h-0 flex-col lg:max-h-none">
          <CardHeader>
            <Button
              type="button"
              onClick={startNewConversation}
              disabled={isSending}
              className="w-full"
            >
              <MessageCirclePlus aria-hidden />
              Cuộc trò chuyện mới
            </Button>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 space-y-1 overflow-y-auto">
            {conversations.data?.map((item) => (
              <div key={item.id} className="flex items-center gap-1">
                <button
                  type="button"
                  disabled={isSending}
                  onClick={() => {
                    clearPendingStreamChunks()
                    setConversationId(item.id)
                    updateConversationUrl(item.id)
                    setIsDraft(false)
                    setPendingQuestion(undefined)
                    setStreamedAnswer("")
                    setStreamedVisualization(undefined)
                    setStreamComplete(false)
                    setStreamStatus("")
                    setSendError(undefined)
                  }}
                  className={`min-w-0 flex-1 truncate rounded-md px-3 py-2 text-left text-sm hover:bg-muted ${
                    item.id === activeConversationId && !isDraft
                      ? "bg-muted font-medium"
                      : ""
                  }`}
                  title={item.title}
                >
                  {item.title}
                </button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Xóa ${item.title}`}
                  disabled={deleteConversation.isPending || isSending}
                  onClick={() => deleteConversation.mutate(item.id)}
                >
                  <Trash2 aria-hidden />
                </Button>
              </div>
            ))}
            {conversations.isLoading ? (
              <p className="text-muted-foreground px-3 py-2 text-sm">Đang tải lịch sử…</p>
            ) : null}
            {conversations.isError ? (
              <p className="text-destructive px-3 py-2 text-sm">
                Không tải được lịch sử: {errorMessage(conversations.error)}
              </p>
            ) : null}
            {deleteConversation.isError ? (
              <p className="text-destructive px-3 py-2 text-sm" role="alert">
                Không xóa được hội thoại: {errorMessage(deleteConversation.error)}
              </p>
            ) : null}
          </CardContent>
        </Card>

        <Card className="flex min-h-0 min-w-0 flex-col">
          <CardHeader className="shrink-0 border-b">
            <CardTitle className="flex items-center gap-2">
              <Bot className="size-5 text-primary" aria-hidden />
              {isDraft ? "Cuộc trò chuyện mới" : conversation.data?.title ?? "EnergySmart"}
            </CardTitle>
            <CardDescription>
              Hội thoại và message được lưu trong MongoDB cùng mã người dùng sở hữu.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden pt-5">
            <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto" aria-live="polite">
              {messages.length === 0 && !showPendingTurn && !(isDraft && isSending) ? (
                <div className="flex flex-1 flex-col items-center justify-center gap-4 py-8 text-center">
                  <MessageCircle className="text-primary size-10" aria-hidden />
                  <div>
                    <p className="font-medium">Bạn muốn tìm hiểu điều gì về năng lượng?</p>
                    <p className="text-muted-foreground mt-1 text-sm">
                      Chọn câu hỏi gợi ý hoặc nhập câu hỏi của bạn.
                    </p>
                  </div>
                  <div className="flex flex-wrap justify-center gap-2">
                    {SUGGESTIONS.map((question) => (
                      <Button
                        key={question}
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={isSending}
                        onClick={() => sendSuggested(question)}
                      >
                        {question}
                      </Button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((message) => {
                  const isUser = message.role === "user"
                  return (
                    <div
                      key={message.id}
                      className={`flex items-start gap-3 ${isUser ? "justify-end" : ""}`}
                    >
                      {isUser ? (
                        <p className="max-w-[85%] rounded-xl bg-primary px-4 py-3 text-sm whitespace-pre-wrap text-primary-foreground">
                          {message.content}
                        </p>
                      ) : (
                        <>
                          <Bot className="text-primary mt-1 size-5 shrink-0" aria-hidden />
                          <div className="flex min-w-0 flex-1 flex-col gap-4">
                            <AssistantMessage content={message.content} />
                            {message.visualization ? (
                              <AnalyticsVisualization data={message.visualization} />
                            ) : null}
                          </div>
                        </>
                      )}
                      {isUser ? (
                        <UserRound className="text-muted-foreground mt-1 size-5 shrink-0" aria-hidden />
                      ) : null}
                    </div>
                  )
                })
              )}
              {showPendingTurn ? (
                <div className="flex items-start justify-end gap-3">
                  <p className="max-w-[85%] rounded-xl bg-primary px-4 py-3 text-sm whitespace-pre-wrap text-primary-foreground">
                    {pendingQuestion}
                  </p>
                  <UserRound
                    className="text-muted-foreground mt-1 size-5 shrink-0"
                    aria-hidden
                  />
                </div>
              ) : null}
              {showPendingTurn && streamedAnswer ? (
                <div className="flex min-w-0 items-start gap-3">
                  <Bot className="text-primary mt-1 size-5 shrink-0" aria-hidden />
                  <div className="flex min-w-0 flex-1 flex-col gap-4">
                    <AssistantMessage content={streamedAnswer} />
                    {streamComplete && streamedVisualization ? (
                      <AnalyticsVisualization data={streamedVisualization} />
                    ) : null}
                  </div>
                </div>
              ) : null}
              {isSending ? (
                <div className="text-muted-foreground flex items-center gap-2 text-sm" role="status">
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                  {streamStatus || "Đang phân tích câu hỏi…"}
                </div>
              ) : null}
              {sendError ? (
                <p className="text-destructive text-sm" role="alert">
                  Không thể trả lời lúc này: {sendError}
                </p>
              ) : null}
              <div ref={endOfMessages} />
            </div>

            <form
              onSubmit={(event) => submitMessage(event)}
              className="flex shrink-0 items-end gap-2 border-t pt-4"
            >
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault()
                    event.currentTarget.form?.requestSubmit()
                  }
                }}
                placeholder="Ví dụ: Tầng nào tiêu thụ nhiều nhất tuần này?"
                aria-label="Câu hỏi cho trợ lý AI"
                maxLength={4000}
                rows={2}
                disabled={isSending}
                className="max-h-36 min-h-12 resize-y"
              />
              <Button type="submit" aria-label="Gửi câu hỏi" disabled={!input.trim() || isSending}>
                {isSending ? (
                  <Loader2 className="animate-spin" aria-hidden />
                ) : (
                  <Send aria-hidden />
                )}
                <span className="sr-only">Gửi</span>
              </Button>
            </form>
            <p className="text-muted-foreground text-xs">
              Lịch sử được lưu bền vững theo tài khoản của bạn.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
