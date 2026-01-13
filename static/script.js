// LinkLog - 前端核心逻辑

const API_BASE = 'http://localhost:8003';

let cy = null;
let currentGraphData = null;

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
});

function initEventListeners() {
    // 标签页切换
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
    
    // URL 输入界面
    const analyzeBtn = document.getElementById('analyze-btn');
    const urlInput = document.getElementById('url-input');
    
    analyzeBtn.addEventListener('click', handleAnalyze);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleAnalyze();
        }
    });
    
    
    // 文本输入界面
    const analyzeTextBtn = document.getElementById('analyze-text-btn');
    const textInput = document.getElementById('text-input');
    
    analyzeTextBtn.addEventListener('click', handleAnalyzeText);
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.metaKey) { // Cmd+Enter 提交
            e.preventDefault();
            handleAnalyzeText();
        }
    });
    
    // 画布界面
    const backBtn = document.getElementById('back-btn');
    const addUrlBtn = document.getElementById('add-url-btn');
    const closeInfoBtn = document.getElementById('close-info');
    
    backBtn.addEventListener('click', () => {
        switchScreen('input');
    });
    addUrlBtn.addEventListener('click', () => {
        showAddUrlModal();
    });
    closeInfoBtn.addEventListener('click', () => {
        hideNodeInfo();
    });
    
    // 模态框
    const modal = document.getElementById('add-url-modal');
    const modalBackdrop = document.getElementById('modal-backdrop');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelBtn = document.getElementById('cancel-btn');
    const confirmAddBtn = document.getElementById('confirm-add-btn');
    const newUrlInput = document.getElementById('new-url-input');
    
    closeModalBtn.addEventListener('click', hideAddUrlModal);
    cancelBtn.addEventListener('click', hideAddUrlModal);
    modalBackdrop.addEventListener('click', hideAddUrlModal);
    confirmAddBtn.addEventListener('click', handleAddUrl);
    newUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleAddUrl();
        }
    });
}

// ==================== 标签页切换 ====================

function switchTab(tab) {
    const urlGroup = document.getElementById('url-input-group');
    const textGroup = document.getElementById('text-input-group');
    const urlInput = document.getElementById('url-input');
    const textInput = document.getElementById('text-input');
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    tabButtons.forEach(btn => {
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    if (tab === 'url') {
        urlGroup.classList.remove('hidden');
        textGroup.classList.add('hidden');
        setTimeout(() => urlInput.focus(), 100);
    } else {
        urlGroup.classList.add('hidden');
        textGroup.classList.remove('hidden');
        setTimeout(() => textInput.focus(), 100);
    }
}

// ==================== 屏幕切换 ====================

function switchScreen(screenName) {
    console.log(`🔄 切换屏幕到: ${screenName}`); // 调试日志
    
    // 获取所有屏幕元素
    const allScreens = document.querySelectorAll('.screen');
    console.log(`找到 ${allScreens.length} 个屏幕元素`);
    
    // 移除所有 active 类
    allScreens.forEach((screen, index) => {
        const hadActive = screen.classList.contains('active');
        screen.classList.remove('active');
        console.log(`  屏幕 ${index + 1} (${screen.id}): 移除 active${hadActive ? ' (之前是 active)' : ''}`);
    });
    
    // 找到目标屏幕
    const targetScreen = document.getElementById(`${screenName}-screen`);
    if (targetScreen) {
        targetScreen.classList.add('active');
        console.log(`✅ 屏幕 ${screenName} 已激活`);
        
        // 验证切换是否成功
        const isActive = targetScreen.classList.contains('active');
        const computedStyle = window.getComputedStyle(targetScreen);
        const display = computedStyle.display;
        const visibility = computedStyle.visibility;
        const opacity = computedStyle.opacity;
        console.log(`   检查结果: active=${isActive}, display=${display}, visibility=${visibility}, opacity=${opacity}`);
        
        // 检查所有屏幕的显示状态
        allScreens.forEach((screen, index) => {
            const screenStyle = window.getComputedStyle(screen);
            console.log(`   屏幕 ${screen.id}: display=${screenStyle.display}, visibility=${screenStyle.visibility}, hasActive=${screen.classList.contains('active')}`);
        });
        
        if (display === 'none' || visibility === 'hidden') {
            console.error(`⚠️  警告: 屏幕已激活但显示属性异常！`);
            console.log(`   尝试强制设置显示属性`);
            targetScreen.style.display = 'flex';
            targetScreen.style.visibility = 'visible';
            targetScreen.style.opacity = '1';
        }
        
        // 强制隐藏所有其他屏幕
        allScreens.forEach(screen => {
            if (screen !== targetScreen) {
                screen.classList.remove('active');
                screen.style.display = 'none';
                screen.style.visibility = 'hidden';
                screen.style.opacity = '0';
                screen.style.pointerEvents = 'none';
                screen.style.zIndex = '0';
                console.log(`   强制隐藏: ${screen.id}`);
            }
        });
        
        // 强制显示目标屏幕
        targetScreen.style.display = 'flex';
        targetScreen.style.visibility = 'visible';
        targetScreen.style.opacity = '1';
        targetScreen.style.pointerEvents = 'auto';
        targetScreen.style.zIndex = '10';
        console.log(`   强制显示: ${targetScreen.id}`);
        
        // 延迟验证，确保切换成功
        setTimeout(() => {
            const inputScreen = document.getElementById('input-screen');
            const canvasScreen = document.getElementById('canvas-screen');
            
            if (screenName === 'canvas' && inputScreen) {
                const inputStyle = window.getComputedStyle(inputScreen);
                if (inputStyle.display !== 'none') {
                    console.error(`❌ input-screen 仍然显示！再次强制隐藏...`);
                    inputScreen.style.cssText = 'display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important; z-index: 0 !important;';
                }
            }
            
            if (canvasScreen) {
                const canvasStyle = window.getComputedStyle(canvasScreen);
                console.log(`   最终验证 - canvas-screen: display=${canvasStyle.display}, visibility=${canvasStyle.visibility}, zIndex=${canvasStyle.zIndex}`);
            }
        }, 100);
    } else {
        console.error(`❌ 找不到屏幕元素: ${screenName}-screen`);
        console.log(`   当前页面中的屏幕元素:`, Array.from(allScreens).map(s => s.id));
    }
    
    if (screenName === 'canvas') {
        console.log('准备初始化 Cytoscape，当前 cy 状态:', cy ? '已初始化' : '未初始化');
        if (!cy) {
            console.log('初始化 Cytoscape...');
            initCytoscape();
        } else {
            console.log('Cytoscape 已存在，跳过初始化');
        }
    }
}

// ==================== 分析课程 ====================

async function handleAnalyze() {
    const urlInput = document.getElementById('url-input');
    const url = urlInput.value.trim();
    
    if (!url) {
        alert('请输入有效的 URL');
        return;
    }
    
    const loadingIndicator = document.getElementById('loading-indicator');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    loadingIndicator.classList.remove('hidden');
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                urls: [url],
                texts: []
            })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            // HTTP 错误响应
            const errorMsg = result.detail || result.error || `HTTP ${response.status} 错误`;
            console.error('API 错误:', result);
            alert('分析失败：' + errorMsg);
            return;
        }
        
        if (result.success) {
            currentGraphData = result.data;
            switchScreen('canvas');
            renderGraph(result.data);
        } else {
            const errorMsg = result.error || result.detail || '未知错误';
            console.error('分析失败:', result);
            alert('分析失败：' + errorMsg);
        }
    } catch (error) {
        console.error('分析错误:', error);
        alert('分析失败：' + (error.message || '网络错误，请检查服务器是否正常运行'));
    } finally {
        loadingIndicator.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
}

// ==================== 分析文本内容 ====================

async function handleAnalyzeText() {
    const textInput = document.getElementById('text-input');
    const text = textInput.value.trim();
    
    if (!text) {
        alert('请输入课程内容文本');
        return;
    }
    
    if (text.length < 50) {
        alert('文本内容太短，请输入至少 50 个字符的课程内容');
        return;
    }
    
    const loadingIndicator = document.getElementById('loading-indicator');
    const analyzeTextBtn = document.getElementById('analyze-text-btn');
    
    loadingIndicator.classList.remove('hidden');
    analyzeTextBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                urls: [],
                texts: [text]
            })
        });
        
        const result = await response.json();
        
        console.log('API 响应:', result); // 调试日志
        
        if (!response.ok) {
            const errorMsg = result.detail || result.error || `HTTP ${response.status} 错误`;
            console.error('API 错误:', result);
            alert('分析失败：' + errorMsg);
            return;
        }
        
        if (result.success) {
            console.log('分析成功，准备跳转到画布');
            console.log('数据:', result.data);
            currentGraphData = result.data;
            switchScreen('canvas');
            // 等待一下确保画布初始化完成
            setTimeout(() => {
                renderGraph(result.data);
            }, 100);
        } else {
            const errorMsg = result.error || result.detail || '未知错误';
            console.error('分析失败:', result);
            alert('分析失败：' + errorMsg);
        }
    } catch (error) {
        console.error('分析错误:', error);
        alert('分析失败：' + (error.message || '网络错误，请检查服务器是否正常运行'));
    } finally {
        loadingIndicator.classList.add('hidden');
        analyzeTextBtn.disabled = false;
    }
}

// ==================== Cytoscape 初始化 ====================

function initCytoscape() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node[type="main"]',
                style: {
                    'background-color': '#007aff',
                    'label': 'data(label)',
                    'width': 80,
                    'height': 80,
                    'shape': 'round-rectangle',
                    'border-width': 2,
                    'border-color': '#0051d5',
                    'font-size': '14px',
                    'font-weight': '600',
                    'color': '#fff',
                    'text-wrap': 'wrap',
                    'text-max-width': '100px',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'padding': '10px'
                }
            },
            {
                selector: 'node[type="dependency"]',
                style: {
                    'background-color': '#ff9500',
                    'label': 'data(label)',
                    'width': 60,
                    'height': 60,
                    'shape': 'ellipse',
                    'border-width': 2,
                    'border-color': '#ff7700',
                    'font-size': '12px',
                    'font-weight': '500',
                    'color': '#fff',
                    'text-wrap': 'wrap',
                    'text-max-width': '80px',
                    'text-valign': 'center',
                    'text-halign': 'center'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#86868b',
                    'target-arrow-color': '#86868b',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(reason)',
                    'font-size': '11px',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -10,
                    'color': '#86868b'
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 3,
                    'border-color': '#007aff',
                    'overlay-opacity': 0.2
                }
            }
        ],
        layout: {
            name: 'breadthfirst',  // 使用默认布局，避免 dagre 依赖问题
            directed: true,
            spacingFactor: 1.5
        }
    });
    
    // 节点点击事件
    cy.on('tap', 'node', (evt) => {
        const node = evt.target;
        showNodeInfo(node.data());
    });
    
    // 画布点击事件（取消选择）
    cy.on('tap', (evt) => {
        if (evt.target === cy) {
            hideNodeInfo();
        }
    });
    
    console.log('✅ Cytoscape 初始化完成');
}

// ==================== 渲染图谱 ====================

function renderGraph(graphData) {
    console.log('开始渲染图谱，数据:', graphData); // 调试日志
    
    if (!cy) {
        console.log('Cytoscape 未初始化，正在初始化...');
        initCytoscape();
    }
    
    if (!cy) {
        console.error('Cytoscape 初始化失败！');
        alert('画布初始化失败，请刷新页面重试');
        return;
    }
    
    // 清空现有内容
    cy.elements().remove();
    
    // 添加节点
    if (graphData.nodes && graphData.nodes.length > 0) {
        console.log(`添加 ${graphData.nodes.length} 个节点`);
        graphData.nodes.forEach(node => {
            cy.add({
                group: 'nodes',
                data: {
                    id: node.id,
                    label: node.label,
                    type: node.type,
                    description: node.description || '',
                    source: node.source || ''
                }
            });
        });
    } else {
        console.warn('没有节点数据或节点数组为空');
    }
    
    // 添加边
    if (graphData.edges && graphData.edges.length > 0) {
        console.log(`添加 ${graphData.edges.length} 条边`);
        graphData.edges.forEach(edge => {
            cy.add({
                group: 'edges',
                data: {
                    id: `e${edge.source}-${edge.target}`,
                    source: edge.source,
                    target: edge.target,
                    reason: edge.reason || '',
                    type: edge.type || 'depends_on'
                }
            });
        });
    } else {
        console.warn('没有边数据或边数组为空');
    }
    
    console.log('图谱元素添加完成，开始布局...');
    
    // 重新布局 - 使用兼容的布局算法
    try {
        // 优先尝试使用 breadthfirst 布局（Cytoscape 内置）
        cy.layout({
            name: 'breadthfirst',
            directed: true,
            spacingFactor: 1.5,
            padding: 30
        }).run();
        console.log('布局完成');
    } catch (e) {
        console.warn('布局算法失败，使用 grid 布局:', e);
        // 如果失败，使用最简单的 grid 布局
        const nodeCount = cy.nodes().length;
        cy.layout({
            name: 'grid',
            rows: nodeCount > 0 ? Math.ceil(Math.sqrt(nodeCount)) : 1,
            cols: nodeCount > 0 ? Math.ceil(Math.sqrt(nodeCount)) : 1,
            padding: 30
        }).run();
    }
    
    // 适应画布
    cy.fit(cy.elements(), 50);
    console.log('图谱渲染完成！');
}

// ==================== 节点信息显示 ====================

function showNodeInfo(nodeData) {
    const nodeInfo = document.getElementById('node-info');
    const nodeTitle = document.getElementById('node-title');
    const nodeContent = document.getElementById('node-content');
    
    nodeTitle.textContent = nodeData.label;
    
    let content = '';
    if (nodeData.description) {
        content += `<p>${nodeData.description}</p>`;
    }
    if (nodeData.source) {
        content += `<p style="margin-top: 12px; font-size: 13px; color: var(--text-secondary);">来源: ${nodeData.source}</p>`;
    }
    if (nodeData.type === 'dependency') {
        content += `<p style="margin-top: 8px; padding: 8px; background: rgba(255, 149, 0, 0.1); border-radius: 6px; font-size: 13px;">💡 这是一个技术依赖，你可以先了解其基本用途，不必深挖细节。</p>`;
    }
    
    nodeContent.innerHTML = content || '<p>暂无详细信息</p>';
    nodeInfo.classList.remove('hidden');
}

function hideNodeInfo() {
    document.getElementById('node-info').classList.add('hidden');
    if (cy) {
        cy.elements().unselect();
    }
}

// ==================== 添加 URL 模态框 ====================

function showAddUrlModal() {
    const modal = document.getElementById('add-url-modal');
    const input = document.getElementById('new-url-input');
    modal.classList.remove('hidden');
    input.value = '';
    input.focus();
}

function hideAddUrlModal() {
    document.getElementById('add-url-modal').classList.add('hidden');
    document.getElementById('modal-loading').classList.add('hidden');
}

async function handleAddUrl() {
    const input = document.getElementById('new-url-input');
    const url = input.value.trim();
    
    if (!url) {
        alert('请输入有效的 URL');
        return;
    }
    
    const modalLoading = document.getElementById('modal-loading');
    const confirmBtn = document.getElementById('confirm-add-btn');
    
    modalLoading.classList.remove('hidden');
    confirmBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/add-url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url
            })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            const errorMsg = result.detail || result.error || `HTTP ${response.status} 错误`;
            console.error('API 错误:', result);
            alert('添加失败：' + errorMsg);
            return;
        }
        
        if (result.success) {
            // 合并新数据到现有图谱
            mergeGraphData(result.data);
            hideAddUrlModal();
        } else {
            const errorMsg = result.error || result.detail || '未知错误';
            console.error('添加失败:', result);
            alert('添加失败：' + errorMsg);
        }
    } catch (error) {
        console.error('添加 URL 错误:', error);
        alert('添加失败：' + (error.message || '网络错误'));
    } finally {
        modalLoading.classList.add('hidden');
        confirmBtn.disabled = false;
    }
}

// ==================== 合并图谱数据 ====================

function mergeGraphData(newData) {
    if (!currentGraphData) {
        currentGraphData = newData;
        renderGraph(newData);
        return;
    }
    
    // 合并节点（避免重复）
    const existingNodeIds = new Set(currentGraphData.nodes.map(n => n.id));
    newData.nodes.forEach(node => {
        if (!existingNodeIds.has(node.id)) {
            currentGraphData.nodes.push(node);
        }
    });
    
    // 合并边
    const existingEdgeIds = new Set(
        currentGraphData.edges.map(e => `${e.source}-${e.target}`)
    );
    newData.edges.forEach(edge => {
        const edgeId = `${edge.source}-${edge.target}`;
        if (!existingEdgeIds.has(edgeId)) {
            currentGraphData.edges.push(edge);
        }
    });
    
    // 重新渲染
    renderGraph(currentGraphData);
}


// ==================== 测试函数 ====================

async function handleTest() {
    console.log('🧪 测试模式：使用固定数据，不调用 AI');
    
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.classList.remove('hidden');
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/analyze-test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        console.log('测试 API 响应:', result);
        
        if (!response.ok) {
            const errorMsg = result.detail || result.error || `HTTP ${response.status} 错误`;
            console.error('测试 API 错误:', result);
            alert('测试失败：' + errorMsg);
            return;
        }
        
        if (result.success) {
            console.log('✅ 测试数据接收成功，准备跳转到画布');
            console.log('数据:', result.data);
            currentGraphData = result.data;
            switchScreen('canvas');
            setTimeout(() => {
                renderGraph(result.data);
            }, 100);
        } else {
            console.error('测试失败:', result);
            alert('测试失败：' + (result.error || '未知错误'));
        }
    } catch (error) {
        console.error('测试错误:', error);
        alert('测试失败：' + (error.message || '网络错误'));
    } finally {
        if (loadingIndicator) {
            loadingIndicator.classList.add('hidden');
        }
    }
}
