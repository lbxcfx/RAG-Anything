<template>
  <div class="chat-container">
    <div class="page-header">
      <h2>智能问答</h2>
      <div class="header-actions">
        <el-button icon="Back" @click="router.back()">返回</el-button>
        <el-button icon="RefreshRight" @click="handleNewChat">新对话</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="session-list">
          <template #header>
            <div class="card-header">
              <span>对话历史</span>
            </div>
          </template>
          <div class="sessions">
            <div
              v-for="session in sessions"
              :key="session.id"
              class="session-item"
              :class="{ active: currentSessionId === session.id }"
              @click="handleSelectSession(session.id)"
            >
              <div class="session-title">{{ session.title || '新对话' }}</div>
              <div class="session-time">{{ formatTime(session.created_at) }}</div>
            </div>
          </div>
          <el-empty v-if="!sessions.length" description="暂无对话" />
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card class="chat-main">
          <template #header>
            <div class="chat-header">
              <div v-if="knowledgeBase">
                <el-icon><FolderOpened /></el-icon>
                {{ knowledgeBase.name }}
              </div>
              <div v-else>无知识库对话</div>
              <el-select v-model="queryMode" placeholder="选择查询模式" style="width: 200px">
                <el-option label="本地模式" value="local" />
                <el-option label="全局模式" value="global" />
                <el-option label="混合模式" value="hybrid" />
                <el-option label="混合+图谱" value="hybrid_graph" />
              </el-select>
            </div>
          </template>

          <div class="messages" ref="messagesRef">
            <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
              <div class="message-content">
                <div class="message-header">
                  <el-avatar :size="32">
                    {{ msg.role === 'user' ? 'U' : 'AI' }}
                  </el-avatar>
                  <span class="message-role">{{ msg.role === 'user' ? '你' : 'AI助手' }}</span>
                </div>
                <div class="message-body">
                  <div v-if="msg.multimodal_content?.length" class="multimodal-content">
                    <div v-for="(item, idx) in msg.multimodal_content" :key="idx" class="multimodal-item">
                      <el-image
                        v-if="item.type === 'image'"
                        :src="item.content"
                        fit="contain"
                        style="max-width: 200px"
                      />
                      <div v-else-if="item.type === 'table'" class="table-content">
                        <el-tag>表格</el-tag>
                      </div>
                      <div v-else-if="item.type === 'equation'" class="equation-content">
                        {{ item.content }}
                      </div>
                    </div>
                  </div>
                  <div class="text-content">{{ msg.content }}</div>
                  <div v-if="msg.sql" class="sql-content">
                    <el-divider content-position="left">生成的SQL</el-divider>
                    <pre>{{ msg.sql }}</pre>
                  </div>
                  <div v-if="msg.chart_url" class="chart-content">
                    <el-divider content-position="left">数据可视化</el-divider>
                    <el-image :src="msg.chart_url" fit="contain" />
                  </div>
                  <div v-if="msg.sources?.length" class="sources">
                    <el-divider content-position="left">参考来源</el-divider>
                    <el-tag
                      v-for="(source, idx) in msg.sources"
                      :key="idx"
                      size="small"
                      style="margin: 4px"
                    >
                      {{ source }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="loading" class="message assistant">
              <div class="message-content">
                <div class="message-header">
                  <el-avatar :size="32">AI</el-avatar>
                  <span class="message-role">AI助手</span>
                </div>
                <div class="message-body">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  正在思考...
                </div>
              </div>
            </div>
          </div>

          <div class="input-area">
            <div class="multimodal-upload" v-if="multimodalFiles.length">
              <div v-for="(file, idx) in multimodalFiles" :key="idx" class="upload-item">
                <el-image
                  v-if="file.type.startsWith('image')"
                  :src="file.preview"
                  fit="contain"
                  style="width: 60px; height: 60px"
                />
                <el-icon class="close-icon" @click="removeMultimodalFile(idx)">
                  <CircleClose />
                </el-icon>
              </div>
            </div>

            <div class="input-wrapper">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleMultimodalUpload"
                accept="image/*"
              >
                <el-button icon="Picture" circle />
              </el-upload>

              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="3"
                placeholder="输入你的问题..."
                @keydown.enter.exact.prevent="handleSend"
              />

              <el-button type="primary" :loading="loading" @click="handleSend">
                <el-icon><Promotion /></el-icon>
                发送
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { knowledgeBaseApi } from '@/api/knowledge-base'
import { queryApi } from '@/api/query'

const route = useRoute()
const router = useRouter()

const kbId = route.params.id ? Number(route.params.id) : null
const knowledgeBase = ref<any>(null)
const sessions = ref<any[]>([])
const currentSessionId = ref<number | null>(null)
const messages = ref<any[]>([])
const queryMode = ref('hybrid')
const inputMessage = ref('')
const loading = ref(false)
const messagesRef = ref<HTMLElement>()
const multimodalFiles = ref<any[]>([])

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const loadKnowledgeBase = async () => {
  if (kbId) {
    try {
      knowledgeBase.value = await knowledgeBaseApi.get(kbId)
    } catch (error) {
      console.error(error)
    }
  }
}

const loadSessions = async () => {
  try {
    const params = kbId ? { kb_id: kbId } : {}
    sessions.value = await queryApi.getSessions(params)
    if (sessions.value.length > 0 && !currentSessionId.value) {
      currentSessionId.value = sessions.value[0].id
    }
  } catch (error) {
    console.error(error)
  }
}

const loadMessages = async () => {
  if (!currentSessionId.value) return
  try {
    const session = await queryApi.getSession(currentSessionId.value)
    messages.value = session.messages || []
    scrollToBottom()
  } catch (error) {
    console.error(error)
  }
}

const handleNewChat = async () => {
  try {
    const session = await queryApi.createSession(kbId || undefined)
    currentSessionId.value = session.id
    messages.value = []
    await loadSessions()
  } catch (error) {
    console.error(error)
  }
}

const handleSelectSession = async (sessionId: number) => {
  currentSessionId.value = sessionId
  await loadMessages()
}

const handleMultimodalUpload = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    multimodalFiles.value.push({
      file: file.raw,
      type: file.raw.type,
      preview: e.target?.result,
    })
  }
  reader.readAsDataURL(file.raw)
}

const removeMultimodalFile = (index: number) => {
  multimodalFiles.value.splice(index, 1)
}

const handleSend = async () => {
  if (!inputMessage.value.trim() && !multimodalFiles.value.length) {
    ElMessage.warning('请输入问题或上传图片')
    return
  }

  if (!currentSessionId.value) {
    await handleNewChat()
  }

  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: inputMessage.value,
    multimodal_content: multimodalFiles.value.map(f => ({
      type: f.type.startsWith('image') ? 'image' : 'file',
      content: f.preview,
    })),
  }

  messages.value.push(userMessage)
  scrollToBottom()

  const question = inputMessage.value
  inputMessage.value = ''
  const multimodal = multimodalFiles.value.map(f => f.file)
  multimodalFiles.value = []

  loading.value = true
  try {
    const response = await queryApi.query(kbId, {
      question,
      mode: queryMode.value,
      session_id: currentSessionId.value!,
      multimodal_content: multimodal.length > 0 ? multimodal : undefined,
    })

    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: response.answer,
      sql: response.sql,
      chart_url: response.chart_url,
      sources: response.sources,
    }

    messages.value.push(assistantMessage)
    scrollToBottom()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

watch(currentSessionId, () => {
  if (currentSessionId.value) {
    loadMessages()
  }
})

onMounted(() => {
  loadKnowledgeBase()
  loadSessions()
})
</script>

<style scoped lang="scss">
.chat-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .session-list {
    height: calc(100vh - 200px);

    .sessions {
      max-height: calc(100vh - 300px);
      overflow-y: auto;

      .session-item {
        padding: 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.3s;

        &:hover {
          background-color: #f5f7fa;
        }

        &.active {
          background-color: #e6f7ff;
        }

        .session-title {
          font-weight: 500;
          margin-bottom: 4px;
        }

        .session-time {
          font-size: 12px;
          color: #999;
        }
      }
    }
  }

  .chat-main {
    height: calc(100vh - 200px);
    display: flex;
    flex-direction: column;

    .chat-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      background-color: #f5f7fa;

      .message {
        margin-bottom: 20px;

        .message-content {
          display: flex;
          gap: 12px;

          .message-header {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;

            .message-role {
              font-size: 12px;
              color: #666;
            }
          }

          .message-body {
            flex: 1;
            background: white;
            padding: 12px;
            border-radius: 8px;

            .multimodal-content {
              display: flex;
              gap: 8px;
              margin-bottom: 8px;
              flex-wrap: wrap;
            }

            .sql-content,
            .chart-content,
            .sources {
              margin-top: 16px;

              pre {
                background: #f5f7fa;
                padding: 12px;
                border-radius: 4px;
                overflow-x: auto;
              }
            }
          }
        }

        &.user {
          .message-content {
            flex-direction: row-reverse;

            .message-body {
              background: #e6f7ff;
            }
          }
        }
      }
    }

    .input-area {
      border-top: 1px solid #eee;
      padding: 16px;

      .multimodal-upload {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;

        .upload-item {
          position: relative;

          .close-icon {
            position: absolute;
            top: -8px;
            right: -8px;
            background: white;
            border-radius: 50%;
            cursor: pointer;
          }
        }
      }

      .input-wrapper {
        display: flex;
        gap: 12px;
        align-items: flex-end;
      }
    }
  }
}
</style>
