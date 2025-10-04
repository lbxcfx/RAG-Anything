<template>
  <div class="graph-visualization">
    <div class="page-header">
      <h2>知识图谱</h2>
      <div class="header-actions">
        <el-button icon="Back" @click="router.back()">返回</el-button>
        <el-button icon="RefreshRight" @click="loadGraph">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="18">
        <el-card class="graph-card">
          <div ref="graphContainer" class="graph-container" v-loading="loading"></div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>图谱统计</span>
            </div>
          </template>
          <div class="stats">
            <div class="stat-item">
              <div class="stat-label">实体数量</div>
              <div class="stat-value">{{ stats.entity_count || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">关系数量</div>
              <div class="stat-value">{{ stats.relation_count || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">实体类型</div>
              <div class="stat-value">{{ stats.entity_types?.length || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">关系类型</div>
              <div class="stat-value">{{ stats.relation_types?.length || 0 }}</div>
            </div>
          </div>

          <el-divider />

          <div class="filters">
            <h4>筛选条件</h4>
            <el-form label-position="top" size="small">
              <el-form-item label="实体类型">
                <el-select
                  v-model="filters.entity_types"
                  multiple
                  placeholder="选择实体类型"
                  style="width: 100%"
                >
                  <el-option
                    v-for="type in stats.entity_types"
                    :key="type"
                    :label="type"
                    :value="type"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="关系类型">
                <el-select
                  v-model="filters.relation_types"
                  multiple
                  placeholder="选择关系类型"
                  style="width: 100%"
                >
                  <el-option
                    v-for="type in stats.relation_types"
                    :key="type"
                    :label="type"
                    :value="type"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="最大节点数">
                <el-slider v-model="filters.limit" :min="10" :max="200" :step="10" show-input />
              </el-form-item>
              <el-button type="primary" style="width: 100%" @click="loadGraph">应用筛选</el-button>
            </el-form>
          </div>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>节点详情</span>
            </div>
          </template>
          <div v-if="selectedNode" class="node-detail">
            <h4>{{ selectedNode.label }}</h4>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="ID">{{ selectedNode.id }}</el-descriptions-item>
              <el-descriptions-item label="类型">
                <el-tag size="small">{{ selectedNode.type }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="描述" v-if="selectedNode.description">
                {{ selectedNode.description }}
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="selectedNode.relations?.length" style="margin-top: 16px">
              <h5>关系</h5>
              <div v-for="rel in selectedNode.relations" :key="rel.id" class="relation-item">
                <el-tag size="small" type="info">{{ rel.type }}</el-tag>
                <span>{{ rel.target }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="点击节点查看详情" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'
import { graphApi } from '@/api/graph'

const route = useRoute()
const router = useRouter()

const kbId = Number(route.params.id)
const graphContainer = ref<HTMLElement>()
const loading = ref(false)
const stats = ref<any>({})
const filters = ref({
  entity_types: [] as string[],
  relation_types: [] as string[],
  limit: 100,
})
const selectedNode = ref<any>(null)

let network: Network | null = null
let nodes: DataSet<any> | null = null
let edges: DataSet<any> | null = null

const loadStats = async () => {
  try {
    stats.value = await graphApi.getStats(kbId)
  } catch (error) {
    console.error(error)
  }
}

const loadGraph = async () => {
  loading.value = true
  try {
    const data = await graphApi.getGraph(kbId, {
      entity_types: filters.value.entity_types.length > 0 ? filters.value.entity_types : undefined,
      relation_types: filters.value.relation_types.length > 0 ? filters.value.relation_types : undefined,
      limit: filters.value.limit,
    })

    // Transform data for vis-network
    const nodesData = data.entities.map((entity: any) => ({
      id: entity.id,
      label: entity.name,
      type: entity.type,
      description: entity.description,
      group: entity.type,
      title: `${entity.name}\n类型: ${entity.type}`,
    }))

    const edgesData = data.relations.map((relation: any) => ({
      id: relation.id,
      from: relation.source,
      to: relation.target,
      label: relation.type,
      arrows: 'to',
    }))

    if (nodes && edges) {
      nodes.clear()
      edges.clear()
      nodes.add(nodesData)
      edges.add(edgesData)
    } else {
      initNetwork(nodesData, edgesData)
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const initNetwork = (nodesData: any[], edgesData: any[]) => {
  if (!graphContainer.value) return

  nodes = new DataSet(nodesData)
  edges = new DataSet(edgesData)

  const options = {
    nodes: {
      shape: 'dot',
      size: 20,
      font: {
        size: 14,
        color: '#333',
      },
      borderWidth: 2,
      shadow: true,
    },
    edges: {
      width: 2,
      color: {
        color: '#848484',
        highlight: '#409eff',
      },
      arrows: {
        to: {
          enabled: true,
          scaleFactor: 0.5,
        },
      },
      font: {
        size: 12,
        align: 'middle',
      },
      smooth: {
        type: 'continuous',
      },
    },
    physics: {
      enabled: true,
      stabilization: {
        iterations: 200,
      },
      barnesHut: {
        gravitationalConstant: -30000,
        centralGravity: 0.3,
        springLength: 150,
        springConstant: 0.04,
      },
    },
    interaction: {
      hover: true,
      navigationButtons: true,
      keyboard: true,
    },
    groups: {
      // Define color schemes for different entity types
      Person: { color: { background: '#97C2FC', border: '#2B7CE9' } },
      Organization: { color: { background: '#FFA807', border: '#FA8E00' } },
      Location: { color: { background: '#7BE141', border: '#4BAE12' } },
      Event: { color: { background: '#FB7E81', border: '#E92F33' } },
      Concept: { color: { background: '#C2FABC', border: '#74D66A' } },
    },
  }

  network = new Network(graphContainer.value, { nodes, edges }, options)

  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      const node = nodes?.get(nodeId)
      if (node) {
        const nodeRelations = edgesData.filter(
          (edge: any) => edge.from === nodeId || edge.to === nodeId
        )
        selectedNode.value = {
          ...node,
          relations: nodeRelations.map((rel: any) => ({
            id: rel.id,
            type: rel.label,
            target: rel.from === nodeId ? nodes?.get(rel.to)?.label : nodes?.get(rel.from)?.label,
          })),
        }
      }
    }
  })

  network.on('doubleClick', (params) => {
    if (params.nodes.length > 0) {
      // Expand node - show connected nodes
      const nodeId = params.nodes[0]
      const connectedNodes = network?.getConnectedNodes(nodeId)
      if (connectedNodes) {
        network?.fit({
          nodes: [nodeId, ...connectedNodes],
          animation: {
            duration: 1000,
            easingFunction: 'easeInOutQuad',
          },
        })
      }
    }
  })
}

onMounted(async () => {
  await loadStats()
  await loadGraph()
})

onUnmounted(() => {
  if (network) {
    network.destroy()
    network = null
  }
})
</script>

<style scoped lang="scss">
.graph-visualization {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .graph-card {
    height: calc(100vh - 200px);

    .graph-container {
      width: 100%;
      height: calc(100vh - 260px);
      border: 1px solid #eee;
      border-radius: 4px;
    }
  }

  .stats {
    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .stat-label {
        color: #666;
        font-size: 14px;
      }

      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: #409eff;
      }
    }
  }

  .filters {
    h4 {
      margin: 0 0 16px 0;
    }
  }

  .node-detail {
    h4 {
      margin: 0 0 12px 0;
    }

    h5 {
      margin: 0 0 8px 0;
    }

    .relation-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px;
      background: #f5f7fa;
      border-radius: 4px;
      margin-bottom: 8px;
    }
  }
}
</style>
