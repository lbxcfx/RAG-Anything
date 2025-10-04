<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>仪表板</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="知识库总数" :value="stats.kbCount">
            <template #prefix>
              <el-icon><FolderOpened /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="文档总数" :value="stats.docCount">
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="模型配置" :value="stats.modelCount">
            <template #prefix>
              <el-icon><Setting /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="今日查询" :value="stats.queryCount">
            <template #prefix>
              <el-icon><ChatDotRound /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card header="最近知识库">
          <el-empty v-if="!recentKBs.length" description="暂无知识库" />
          <div v-else class="kb-list">
            <div
              v-for="kb in recentKBs"
              :key="kb.id"
              class="kb-item"
              @click="() => router.push(`/knowledge-bases/${kb.id}/chat`)"
            >
              <el-icon><FolderOpened /></el-icon>
              <div class="kb-info">
                <div class="kb-name">{{ kb.name }}</div>
                <div class="kb-desc">{{ kb.description || '暂无描述' }}</div>
              </div>
              <el-tag>{{ kb.document_count }} 文档</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card header="快速开始">
          <div class="quick-actions">
            <el-button type="primary" icon="Plus" @click="router.push('/knowledge-bases')">
              创建知识库
            </el-button>
            <el-button icon="Setting" @click="router.push('/models')"> 配置模型 </el-button>
            <el-button icon="Document" @click="router.push('/knowledge-bases')"> 上传文档 </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { knowledgeBaseApi } from '@/api/knowledge-base'
import { modelsApi } from '@/api/models'
import { documentsApi } from '@/api/documents'

const router = useRouter()

const stats = ref({
  kbCount: 0,
  docCount: 0,
  modelCount: 0,
  queryCount: 0,
})

const recentKBs = ref<any[]>([])

onMounted(async () => {
  try {
    const [kbs, models, docs] = await Promise.all([
      knowledgeBaseApi.list(),
      modelsApi.list(),
      documentsApi.list(),
    ])

    stats.value.kbCount = kbs.length
    stats.value.modelCount = models.length
    stats.value.docCount = docs.length
    recentKBs.value = kbs.slice(0, 5)
  } catch (error) {
    console.error(error)
  }
})
</script>

<style scoped lang="scss">
.dashboard {
  .stat-card {
    :deep(.el-statistic__head) {
      font-size: 14px;
      color: #666;
    }
  }

  .kb-list {
    .kb-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: background-color 0.3s;

      &:hover {
        background-color: #f5f7fa;
      }

      .kb-info {
        flex: 1;

        .kb-name {
          font-weight: 500;
          margin-bottom: 4px;
        }

        .kb-desc {
          font-size: 12px;
          color: #999;
        }
      }
    }
  }

  .quick-actions {
    display: flex;
    gap: 12px;
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }
}
</style>
