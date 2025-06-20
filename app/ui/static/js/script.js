document.addEventListener('DOMContentLoaded', function () {
    // 全局变量
    let processedImages = [];
    let processedImagesXyxy = {}; // 存储每个图片的xyxy信息
    let inputFolder = '';
    let selectedImagesForTags = [];
    let currentEditingImage = null;
    let fabricCanvas = null;
    let currentOutputSize = 768;
    let currentOutputFolder = '';
    let threshold = 0.3; // 阈值
    let isErasing = false;  // 标记是否正在擦除
    let eraseBrush = null;  // 橡皮擦
    let isBrushing = false;  // 标记是否正在画
    let brushSize = 15;  // 笔刷大小

    // 在全局变量部分添加
    let cursorCanvas = null;
    let cursorVisible = false;

    // 初始化Fabric.js画布
    function initFabricCanvas() {
        fabricCanvas = new fabric.Canvas('image-editor-canvas', {
            backgroundColor: 'white',
            selection: false,
            // 添加以下光标样式设置
            // hoverCursor: 'none',
            // moveCursor: 'none'
        });

        // 在initFabricCanvas函数中添加
        cursorCanvas = document.createElement('canvas');
        cursorCanvas.style.position = 'absolute';
        cursorCanvas.style.pointerEvents = 'none';
        cursorCanvas.style.zIndex = '1000';
        document.body.appendChild(cursorCanvas);

        // 添加更新光标位置的函数
        function updateCursor(x, y, size) {
            const ctx = cursorCanvas.getContext('2d');
            cursorCanvas.width = size * 2;
            cursorCanvas.height = size * 2;
            ctx.clearRect(0, 0, cursorCanvas.width, cursorCanvas.height);

            // 绘制带阴影的圆形光标
            ctx.shadowColor = 'rgba(0,0,0,0.5)';
            ctx.shadowBlur = 5;
            ctx.beginPath();
            ctx.arc(size, size, size / 2, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.fill();
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 1;
            ctx.stroke();

            // 获取页面滚动偏移量
            const scrollX = window.scrollX || window.pageXOffset;
            const scrollY = window.scrollY || window.pageYOffset;

            cursorCanvas.style.left = (x + scrollX - size) + 'px';
            cursorCanvas.style.top = (y + scrollY - size) + 'px';
            cursorVisible = true;
        }

        // 在画布鼠标移动事件中添加光标跟踪
        fabricCanvas.on('mouse:move', function (options) {
            if (isBrushing || isErasing) {
                cursorCanvas.style.display = 'block';
                updateCursor(options.e.clientX, options.e.clientY, brushSize);
            } else if (cursorVisible) {
                cursorCanvas.style.display = 'none';
                cursorVisible = false;
            }
        });


        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        function resizeCanvas() {
            const canvasWrapper = document.querySelector('.canvas-wrapper');
            const size = Math.min(canvasWrapper.clientWidth, canvasWrapper.clientHeight, currentOutputSize); // 确保画布大小不超过容器
            fabricCanvas.setWidth(size == 0 ? currentOutputSize : size);
            fabricCanvas.setHeight(size == 0 ? currentOutputSize : size);

            if (fabricCanvas.getObjects().length > 0) {
                const img = fabricCanvas.getObjects()[0];
                img.set({
                    left: size / 2,
                    top: size / 2,
                    originX: 'center',
                    originY: 'center'
                });
                fabricCanvas.renderAll();
            }
        }
    }

    // 显示加载状态
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(loadingDiv);
    }

    // 隐藏加载状态
    function hideLoading() {
        const loadingDiv = document.querySelector('.loading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    // API调用函数
    async function normalizeImages() {
        inputFolder = document.getElementById('input-folder').value;
        const outputFolder = document.getElementById('output-folder').value;
        // const bgType = document.querySelector('input[name="bg-type"]:checked').value;
        const classes = document.getElementById('detection-classes').value.split(',').map(className => className.trim()).filter(className => className !== '');
        // 去除前后空格，并过滤空字符串
        const reserves = document.getElementById('reserved-classes').value.split(',').map(className => className.trim()).filter(className => className !== '');
        // 判断 reserves 需要包含在 classes 中
        if (reserves.length > 0) {
            if (!reserves.every(className => classes.includes(className))) {
                alert('reserves 需要包含在 classes 中');
                return false;
            }
        }
        const removeFace = document.getElementById('remove-face').checked;
        currentOutputSize = parseInt(document.getElementById('output-size').value);

        if (!inputFolder || inputFolder.length === 0) {
            alert('请选择原始文件夹');
            return false;
        }

        if (!outputFolder) {
            alert('请指定输出文件夹');
            return false;
        }

        currentOutputFolder = outputFolder;

        const requestData = {
            input_folder: inputFolder,
            output_folder: outputFolder,
            width: currentOutputSize,
            height: currentOutputSize,
            broder: 20,
            classes: classes,
            reserves: reserves,
            remove_face: removeFace,
            threshold: threshold
        };

        showLoading();

        try {
            const response = await fetch('/api/image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (result.code === 10000) {
                processedImagesXyxy = {};
                result.data.forEach((img, index) => {
                    processedImagesXyxy[img.image_name.toLowerCase()] = {
                        xyxy: img.xyxy,
                        path: img.path
                    }
                })

                // 图片处理区，显示处理后的文件夹路径
                document.getElementById('processed-folder').value = currentOutputFolder;
                // 标签处理区，显示处理后的文件夹路径
                document.getElementById('tags-folder').value = currentOutputFolder;
                // 加载处理后的图片
                await loadProcessedImages(outputFolder);
                switchTab('bg-removal');
                return true;
            } else {
                alert('图片归一化失败: ' + (result.message || '未知错误'));
                return false;
            }
        } catch (error) {
            alert('API调用失败: ' + error.message);
            return false;
        } finally {
            hideLoading();
        }
    }

    // 加载处理后的图片
    // 在文件顶部添加翻译方法
    async function translateTags(tags, lang = 'zh-CN') {
        if (!tags || tags.length === 0) {
            return {};
        }

        try {
            // 调用翻译API /api/translate，传入tags和lang，所有的参数都为query参数
            // tags为数组，lang为字符串
            // 示例：/api/translate?lang=zh-CN&tags=tag1,tag2,tag3
            // 返回值为json，示例：{"tag1":"翻译1","tag2":"翻译2","tag3":"翻译3"}
            // 拼接url
            const url = '/api/translate?lang=' + lang + '&tags=' + tags.join('&tags=');
            const response = await fetch(url, {
                method: 'GET'
            });

            const result = await response.json();
            if (result.code === 10000) {
                return result.data;
            } else {
                console.error('翻译失败:', result.message || '未知错误');
                return {};
            }
        } catch (error) {
            console.error('翻译API调用失败:', error);
            return {};
        }
    }

    // 修改loadProcessedImages中的翻译调用部分
    async function loadProcessedImages(folderPath) {
        // 清空标签处理的图片列表
        document.getElementById('tag-images-container').innerHTML = '';
        selectedImagesForTags = [];
        // 清空图片列表
        document.getElementById('processed-images-container').innerHTML = '';
        // tags-folder 赋值
        document.getElementById('tags-folder').value = folderPath;
        processedImages = [];
        // 实际项目中这里需要调用API获取处理后的图片列表 /image/list
        // folderPath urlencode
        const response = await fetch('/api/image/list?folder_path=' + encodeURIComponent(folderPath), {
            method: 'GET'
        });
        const result = await response.json();
        processedImages = [];
        if (result.code === 10000) {
            processedImages = result.data.map((img, index) => ({
                id: img.toLowerCase(),
                name: img,
                // 增加时间戳，防止缓存
                src: "/api/image?image_path=" + encodeURIComponent(folderPath + "/" + img) + "&time=" + new Date().getTime(), // 这里假设path是图片的URL
                tags: [] // 初始标签为空
            }));
        } else {
            alert('加载图片列表失败:' + (result.message || '未知错误'));
            return false;
        }


        // 加载标签数据时自动翻译
        try {
            const translatedTags = await translateTags(
                processedImages.flatMap(img => img.tags),
                document.getElementById('translate-lang').value
            );

            processedImages.forEach(img => {
                img.translatedTags = img.tags.map(tag => translatedTags[tag] || tag);
            });
        } catch (error) {
            console.error('翻译失败:', error);
        }

        // 这里模拟从已选择的文件中加载

        const container = document.getElementById('processed-images-container');
        container.innerHTML = '';
        const maxFiles = Math.min(processedImages.length, 100); // 限制加载数量


        for (let i = 0; i < maxFiles; i++) {
            createImageElement(processedImages[i].id, processedImages[i].src, 'processed-images-container', openImageForEditing);

            // 同时添加到标签处理的图片列表
            createImageElement(processedImages[i].id, processedImages[i].src, 'tag-images-container', toggleImageSelectionForTags);
        }
    }

    // 创建图片元素
    function createImageElement(id, src, containerId, clickHandler) {
        const container = document.getElementById(containerId);

        const imgElement = document.createElement('div');
        imgElement.className = 'image-item';
        imgElement.dataset.id = id;

        const img = document.createElement('img');
        img.src = src;
        img.alt = 'Processed image ' + id;

        imgElement.appendChild(img);
        imgElement.addEventListener('click', function () {
            clickHandler(id);
        });
        // 增加删除按钮
        // <div class="image-actions">
        // <button class="delete-btn" title="删除图片">×</button>
        // </div>
        const imgActions = document.createElement('div');
        imgActions.className = 'image-actions';
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.title = '删除图片';
        deleteBtn.textContent = 'x';
        deleteBtn.addEventListener('click', async function (e) {
            // 阻止事件冒泡
            e.stopPropagation();
            if (confirm('确定删除这张图片吗？')) {
                try {
                    const response = await fetch(src, {
                        method: 'DELETE'
                    });
                    const result = await response.json();
                    if (result.code === 10000) {
                        alert('删除成功');
                        // 从列表中删除图片
                        const index = processedImages.findIndex(img => img.id === id);
                        if (index !== -1) {
                            processedImages.splice(index, 1);
                            imgElement.remove();
                        }
                    }
                } catch (error) {
                    console.error('删除失败:', error);
                    alert('删除失败');
                }
            }
        })
        imgActions.appendChild(deleteBtn);
        imgElement.appendChild(imgActions);
        container.appendChild(imgElement);
    }

    // 打开图片进行编辑
    function openImageForEditing(imageId) {
        const imageData = processedImages.find(img => img.id === imageId);
        if (!imageData) return;

        currentEditingImage = imageId;
        fabricCanvas.clear();

        // 获取图片的xyxy坐标
        const xyxyOb = processedImagesXyxy[imageData.id.toLowerCase()]; // 使用id作为key
        let xyxy;
        let src;
        if (xyxyOb) {
            xyxy = xyxyOb.xyxy;
            src = "/api/image?image_path=" + encodeURIComponent(xyxyOb.path) + "&time=" + new Date().getTime();
        } else {
            src = imageData.src + "&time=" + new Date().getTime();
            xyxy = [0, 0, currentOutputSize, currentOutputSize]; // 默认值
        }
        showLoading();
        // 使用fabric加载图片
        fabric.Image.fromURL(src, function (img) {
            const size = Math.min(fabricCanvas.getWidth(), fabricCanvas.getHeight());

            // 计算裁剪区域
            const cropRect = {
                left: xyxy[0],
                top: xyxy[1],
                width: xyxy[2] - xyxy[0],
                height: xyxy[3] - xyxy[1]
            };

            // 创建裁剪后的图片
            const croppedImg = new fabric.Image(img.getElement(), {
                left: size / 2,
                top: size / 2,
                originX: 'center',
                originY: 'center',
            });

            // 计算缩放比例以适应画布
            const scale = Math.min(
                size / cropRect.width,
                size / cropRect.height
            );

            croppedImg.scale(scale);
            fabricCanvas.add(croppedImg);
            fabricCanvas.setActiveObject(croppedImg);
            fabricCanvas.renderAll();
        });
        // 等待图片加载完成后再进行裁剪
        setTimeout(() => {
            hideLoading();
        }, 300);
        // 高亮选中的图片
        document.querySelectorAll('#processed-images-container .image-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`#processed-images-container .image-item[data-id="${imageId}"]`).classList.add('selected');
    }

    // 保存图片修改
    async function saveImageChanges() {
        if (!currentEditingImage) {
            alert('没有正在编辑的图片');
            return;
        }

        const imageData = processedImages.find(img => img.id === currentEditingImage);
        if (!imageData) return;

        // 获取Canvas中的图片数据
        const canvas = document.getElementById('image-editor-canvas');
        // canvas 导出时设置背景为白色
        const imageUrl = canvas.toDataURL('image/png');

        // 更新内存中的图片数据
        imageData.src = imageUrl;

        // 更新显示的图片
        const imgElement = document.querySelector(`#processed-images-container .image-item[data-id="${currentEditingImage}"] img`);
        imgElement.src = imageUrl;

        // 更新标签处理区的图片
        const tagImgElement = document.querySelector(`#tag-images-container .image-item[data-id="${currentEditingImage}"] img`);
        if (tagImgElement) {
            tagImgElement.src = imageUrl;
        }

        // 调用API更新图片
        showLoading();

        try {
            // 模拟FormData创建
            const blob = await (await fetch(imageUrl)).blob();
            const formData = new FormData();
            formData.append('file', blob, imageData.name);

            const response = await fetch(`/api/image?folder_path=${encodeURIComponent(currentOutputFolder)}&image_name=${encodeURIComponent(imageData.name)}`, {
                method: 'PUT',
                body: formData
            });

            const result = await response.json();

            if (result.code !== 10000) {
                alert('图片更新失败: ' + (result.message || '未知错误'));
            }
        } catch (error) {
            alert('API调用失败: ' + error.message);
        } finally {
            hideLoading();
        }
        // 重置橡皮擦状态
        isErasing = false;
        document.getElementById('erase-btn').classList.remove('active');
        // 重置画笔状态
        isBrushing = false;
        document.getElementById('brush-btn').classList.remove('active');
        fabricCanvas.isDrawingMode = false;
    }
    // 新增功能1：生成蒙层图像（白色背景+现有）
    function generateMaskImage() {
        const canvas = document.getElementById('image-editor-canvas');
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = canvas.width;
        tempCanvas.height = canvas.height;
        const tempCtx = tempCanvas.getContext('2d');

        // 黑色背景
        tempCtx.fillStyle = '#000000';
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);

        // 白色画笔内容
        tempCtx.globalCompositeOperation = 'destination-in';
        tempCtx.drawImage(canvas, 0, 0);

        // 恢复默认合成模式
        tempCtx.globalCompositeOperation = 'source-over';

        return tempCanvas.toDataURL('image/png');
    }
    // 图片选择/取消选择（用于标签处理）
    function toggleImageSelectionForTags(imageId) {
        const index = selectedImagesForTags.indexOf(imageId);
        const imgElement = document.querySelector(`#tag-images-container .image-item[data-id="${imageId}"]`);

        if (index === -1) {
            selectedImagesForTags.push(imageId);
            imgElement.classList.add('selected');
        } else {
            selectedImagesForTags.splice(index, 1);
            imgElement.classList.remove('selected');
        }

        updateTagsDisplay();
    }

    // 更新标签显示
    function updateTagsDisplay() {
        const tagsContainer = document.getElementById('tags-container');
        const infoElement = document.getElementById('selected-images-info');

        tagsContainer.innerHTML = '';

        if (selectedImagesForTags.length === 0) {
            infoElement.textContent = '未选择任何图片';
            return;
        }

        infoElement.textContent = `已选择 ${selectedImagesForTags.length} 张图片`;

        // 获取所有选中图片的共同标签
        let commonTags = [];
        if (selectedImagesForTags.length > 0) {
            commonTags = [...processedImages.find(img => img.id === selectedImagesForTags[0]).tags];

            for (let i = 1; i < selectedImagesForTags.length; i++) {
                const imgTags = processedImages.find(img => img.id === selectedImagesForTags[i]).tags;
                commonTags = commonTags.filter(tag => imgTags.includes(tag));
            }
        }

        // 显示标签
        commonTags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'tag';

            // 查找第一个包含此tag的图片以获取翻译
            const imgWithTag = processedImages.find(img =>
                selectedImagesForTags.includes(img.id) && img.tags.includes(tag)
            );
            const translatedTag = imgWithTag?.translatedTags?.[imgWithTag.tags.indexOf(tag)] || tag;

            tagElement.innerHTML = `${translatedTag} <span class="delete-tag" data-tag="${tag}">×</span>`;
            tagsContainer.appendChild(tagElement);

            // 添加删除标签事件
            tagElement.querySelector('.delete-tag').addEventListener('click', function (e) {
                e.stopPropagation();
                removeTagFromSelectedImages(tag);
            });
        });


    }

    // 从选中图片中移除标签
    function removeTagFromSelectedImages(tag) {
        selectedImagesForTags.forEach(imageId => {
            const image = processedImages.find(img => img.id === imageId);
            if (image) {
                const index = image.tags.indexOf(tag);
                if (index !== -1) {
                    image.tags.splice(index, 1);
                }
            }
        });
        updateTagsDisplay();
    }

    // 添加召唤词到标签
    function addSummonWords() {
        const summonWordsInput = document.getElementById('summon-words');
        const words = summonWordsInput.value.split(',').map(w => w.trim()).filter(w => w);

        if (words.length === 0 || selectedImagesForTags.length === 0) {
            return;
        }

        selectedImagesForTags.forEach(imageId => {
            const image = processedImages.find(img => img.id === imageId);
            if (image) {
                words.forEach(word => {
                    if (!image.tags.includes(word)) {
                        image.tags.push(word);
                    }
                });
            }
        });

        summonWordsInput.value = '';
        updateTagsDisplay();
    }

    // 保存标签修改
    async function saveTagsChanges() {
        if (selectedImagesForTags.length === 0) {
            alert('请选择至少一张图片');
            return;
        }

        const filterWordsInput = document.getElementById('filter-words');
        const filterWords = filterWordsInput.value.split(',').map(w => w.trim()).filter(w => w);

        // 应用过滤词
        if (filterWords.length > 0) {
            selectedImagesForTags.forEach(imageId => {
                const image = processedImages.find(img => img.id === imageId);
                if (image) {
                    image.tags = image.tags.filter(tag => !filterWords.includes(tag));
                }
            });
        }

        // 准备API请求数据
        const requestData = {
            folder: currentOutputFolder,
            data: selectedImagesForTags.map(imageId => {
                const image = processedImages.find(img => img.id === imageId);
                return {
                    image_name: image.name,
                    tags: image.tags
                };
            })
        };

        showLoading();

        try {
            const response = await fetch('/api/tags', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (result.code === 10000) {
                alert('标签保存成功');
            } else {
                alert('标签保存失败: ' + (result.message || '未知错误'));
            }
        } catch (error) {
            alert('API调用失败: ' + error.message);
        } finally {
            hideLoading();
        }
    }

    // 获取标签数据并跳转到标签处理页面
    async function goToTagsProcessing() {
        showLoading();
        if (processedImages.length === 0) {
            // 加载图片数据
            await loadProcessedImages(currentOutputFolder);
        }
        try {
            const response = await fetch(`/api/tags?folder=${encodeURIComponent(currentOutputFolder)}&remove_tags=face`);
            const result = await response.json();

            if (result.code === 10000) {
                // 更新内存中的标签数据
                result.data.data.forEach(item => {
                    const image = processedImages.find(img => img.name === item.image_name);
                    if (image) {
                        image.tags = item.tags;
                    }
                });
                // 在实际应用中，这里会使用API返回的数据更新界面
                switchTab('image-processing');
            } else {
                alert('获取标签数据失败: ' + (result.message || '未知错误'));
            }
        } catch (error) {
            alert('API调用失败: ' + error.message);
        } finally {
            hideLoading();
        }
    }

    // 新增选项卡切换函数
    function switchTab(tabId) {
        // 获取所有选项卡按钮和内容
        const tabs = ['bg-removal', 'image-processing', 'tag-processing'];
        const currentIndex = tabs.indexOf(tabId);
        const nextTabId = tabs[(currentIndex + 1) % tabs.length];

        // 更新按钮和内容状态
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.target === nextTabId) {
                btn.classList.add('active');
            }
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            if (content.id === nextTabId) {
                content.classList.add('active');
            }
        });
    }

    // 初始化事件监听
    // 在 initEventListeners 中添加选项卡切换事件
    function initEventListeners() {
        // 初始阈值控件
        document.getElementById('threshold').addEventListener('input', function (e) {
            threshold = e.target.value;
            document.getElementById('threshold-value').textContent = threshold;
        });

        // 背景去除部分
        document.getElementById('normalize-btn').addEventListener('click', normalizeImages);

        // 图片处理部分
        document.getElementById('rotate-left-btn').addEventListener('click', function () {
            const obj = fabricCanvas.getActiveObject();
            if (obj) {
                obj.rotate(obj.angle - 15);
                fabricCanvas.renderAll();
            }
        });

        document.getElementById('rotate-right-btn').addEventListener('click', function () {
            const obj = fabricCanvas.getActiveObject();
            if (obj) {
                obj.rotate(obj.angle + 15);
                fabricCanvas.renderAll();
            }
        });

        document.getElementById('zoom-in-btn').addEventListener('click', function () {
            const obj = fabricCanvas.getActiveObject();
            if (obj) {
                obj.scaleX *= 1.1;
                obj.scaleY *= 1.1;
                fabricCanvas.renderAll();
            }
        });

        document.getElementById('zoom-out-btn').addEventListener('click', function () {
            const obj = fabricCanvas.getActiveObject();
            if (obj) {
                obj.scaleX *= 0.9;
                obj.scaleY *= 0.9;
                fabricCanvas.renderAll();
            }
        });

        document.getElementById('crop-btn').addEventListener('click', function () {
            alert('裁剪功能将在完整版本中实现');
        });

        document.getElementById('reset-btn').addEventListener('click', function () {
            if (currentEditingImage) {
                openImageForEditing(currentEditingImage);
            }
        });

        document.getElementById('save-btn').addEventListener('click', saveImageChanges);
        document.getElementById('next-to-tags-btn').addEventListener('click', goToTagsProcessing);

        // 标签处理部分
        document.getElementById('select-all').addEventListener('change', function (e) {
            const checkboxes = document.querySelectorAll('#tag-images-container .image-item');
            checkboxes.forEach(item => {
                const imageId = item.dataset.id;
                const index = selectedImagesForTags.indexOf(imageId);

                if (e.target.checked && index === -1) {
                    selectedImagesForTags.push(imageId);
                    item.classList.add('selected');
                } else if (!e.target.checked && index !== -1) {
                    selectedImagesForTags.splice(index, 1);
                    item.classList.remove('selected');
                }
            });

            updateTagsDisplay();
        });

        document.getElementById('add-summon-btn').addEventListener('click', addSummonWords);
        document.getElementById('save-tags-btn').addEventListener('click', saveTagsChanges);

        // 允许按Enter键添加召唤词
        document.getElementById('summon-words').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                addSummonWords();
            }
        });
        // 选项卡切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                // 移除所有激活状态
                document.querySelectorAll('.tab-btn, .tab-content').forEach(el => {
                    el.classList.remove('active');
                });

                // 设置当前激活状态
                this.classList.add('active');
                document.getElementById(this.dataset.target).classList.add('active');
            });
        });
        // 初始化画笔大小控件
        document.getElementById('brush-size').addEventListener('input', function (e) {
            brushSize = parseInt(e.target.value);
            document.getElementById('brush-size-label').textContent = brushSize + 'px';

            if (isBrushing || isErasing) {
                fabricCanvas.freeDrawingBrush.width = brushSize;
            }
        });


        // 橡皮擦
        document.getElementById('erase-btn').addEventListener('click', function () {
            isErasing = !isErasing;
            this.classList.toggle('active', isErasing);
            // 取消画笔
            isBrushing = false;
            document.getElementById('brush-btn').classList.remove('active');
            if (isErasing) {
                //取消当前选中对象
                fabricCanvas.discardActiveObject();
                fabricCanvas.requestRenderAll();
                fabricCanvas.isDrawingMode = true;
                fabricCanvas.freeDrawingBrush = eraseBrush || new fabric.PencilBrush(fabricCanvas);
                // 设置橡皮擦颜色为白色
                fabricCanvas.freeDrawingBrush.color = '#ffffff';
                fabricCanvas.freeDrawingBrush.globalCompositeOperation = 'destination-out';
                fabricCanvas.freeDrawingBrush.width = brushSize;
                fabricCanvas.freeDrawingBrush.strokeLineCap = 'round';  // 圆形笔触
                fabricCanvas.freeDrawingBrush.strokeLineJoin = 'round';  // 圆形连接
            } else {
                fabricCanvas.freeDrawingBrush.color = document.getElementById('brush-color').value;
                fabricCanvas.isDrawingMode = false;
            }
        });

        // 初始化颜色选择器事件监听
        document.getElementById('brush-color').addEventListener('input', function (e) {
            if (isBrushing) {
                fabricCanvas.freeDrawingBrush.color = e.target.value;
            }
        });

        // 添加画笔按钮事件
        document.getElementById('brush-btn').addEventListener('click', function () {
            isBrushing = !isBrushing;
            this.classList.toggle('active', isBrushing);
            // 取消橡皮擦
            isErasing = false;
            document.getElementById('erase-btn').classList.remove('active');
            if (isBrushing) {
                //取消当前选中对象
                fabricCanvas.discardActiveObject();
                fabricCanvas.requestRenderAll();
                fabricCanvas.isDrawingMode = true;
                fabricCanvas.isDrawingMode = true;
                fabricCanvas.freeDrawingBrush.color = document.getElementById('brush-color').value;
                fabricCanvas.freeDrawingBrush.globalCompositeOperation = 'source-over';
                fabricCanvas.freeDrawingBrush.width = brushSize;
                fabricCanvas.freeDrawingBrush.strokeLineCap = 'round';  // 圆形笔触
                fabricCanvas.freeDrawingBrush.strokeLineJoin = 'round';  // 圆形连接
            } else {
                fabricCanvas.isDrawingMode = false;
            }
        });

        // 图片处理区 - 加载已处理图片
        document.getElementById('load-processed-btn').addEventListener('click', function () {
            currentOutputFolder = document.getElementById('processed-folder').value;
            if (!currentOutputFolder) {
                alert('请输入文件夹路径');
                return;
            }
            loadProcessedImages(currentOutputFolder);
        });
        // 标签处理区 - 加载标签
        document.getElementById('load-tags-btn').addEventListener('click', function () {
            currentOutputFolder = document.getElementById('tags-folder').value;
            if (!currentOutputFolder) {
                alert('请输入文件夹路径');
                return;
            }
            goToTagsProcessing();
        });

        // 添加翻译按钮事件
        document.getElementById('translate-btn').addEventListener('click', async function () {
            if (selectedImagesForTags.length === 0) {
                alert('请先选择要翻译的图片');
                return;
            }

            const lang = document.getElementById('translate-lang').value;
            const tagsToTranslate = [...new Set(
                selectedImagesForTags.flatMap(id => {
                    const img = processedImages.find(i => i.id === id);
                    return img ? img.tags : [];
                })
            )];

            try {
                const translatedTags = await translateTags(tagsToTranslate, lang);

                // 更新翻译结果
                processedImages.forEach(img => {
                    if (selectedImagesForTags.includes(img.id)) {
                        img.translatedTags = img.tags.map(tag => translatedTags[tag] || tag);
                    }
                });

                updateTagsDisplay();
            } catch (error) {
                alert('翻译失败: ' + error.message);
            }
        });

        // 初始化两个标签输入
        initTagInput('detection-search', 'detection-results', 'detection-tags-container');
        initTagInput('reserved-search', 'reserved-results', 'reserved-tags-container');
    
    }

    // 初始化标签功能
    function initTagInput(searchInputId, resultsId, tagsContainerId) {
        const searchInput = document.getElementById(searchInputId);
        const results = document.getElementById(resultsId);
        const tagsContainer = document.getElementById(tagsContainerId);

        // 从输入框获取当前标签值
        const originalInput = document.getElementById(searchInputId.replace('-search', '-classes'));
        const initialTags = originalInput.value.split(',').filter(tag => tag.trim());

        // 初始化标签
        initialTags.forEach(tag => addTag(tag, tagsContainer));

        // 搜索输入事件
        searchInput.addEventListener('input', async (e) => {
            const query = e.target.value.trim();
            if (query.length < 1) {
                results.style.display = 'none';
                return;
            }

            try {
                const response = await fetch(`/api/nouns?query=${encodeURIComponent(query)}`);
                const result = await response.json();
                if (result.code !== 10000) {
                    throw new Error(result.message || '搜索失败'); 
                }
                const data = result.data || [];
                results.innerHTML = '';
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.textContent = item;
                    div.addEventListener('click', () => {
                        addTag(item, tagsContainer);
                        searchInput.value = '';
                        results.style.display = 'none';
                    });
                    results.appendChild(div);
                });

                results.style.display = data.length ? 'block' : 'none';
            } catch (error) {
                console.error('搜索失败:', error);
            }
        });

        // 点击外部关闭搜索结果
        document.addEventListener('click', (e) => {
            if (!e.target.closest(`#${searchInputId}, #${resultsId}`)) {
                results.style.display = 'none';
            }
        });
    }

    // 添加标签
    function addTag(tag, container) {
        if (!tag.trim()) return;

        const tagElement = document.createElement('span');
        tagElement.className = 'tag-item';
        tagElement.innerHTML = `
        ${tag.trim()}
        <span class="delete-tag">×</span>
    `;

        tagElement.querySelector('.delete-tag').addEventListener('click', () => {
            tagElement.remove();
            updateHiddenInput(container);
        });

        container.appendChild(tagElement);
        updateHiddenInput(container);
    }

    // 更新隐藏的输入值
    function updateHiddenInput(container) {
        const tags = Array.from(container.querySelectorAll('.tag-item'))
            .map(tag => tag.textContent.replace('×', '').trim())
            .filter(tag => tag);

        const inputId = container.id.replace('-tags-container', '-classes');
        document.getElementById(inputId).value = tags.join(',');
    }

    // 初始化应用
    // 在initApp函数中添加状态检查
    function initApp() {
        initFabricCanvas();
        initEventListeners();
        checkServiceStatus();
        // 每30秒检查一次服务状态
        setInterval(checkServiceStatus, 30000);
    }

    // 添加服务状态检查函数
    async function checkServiceStatus() {
        try {
            const response = await fetch('/api/health');
            const result = await response.json();
            const statusTag = document.getElementById('status-tag');

            if (result.code === 10000) {
                statusTag.textContent = '运行中';
                statusTag.className = 'status-tag status-online';
            } else {
                statusTag.textContent = '离线';
                statusTag.className = 'status-tag status-offline';
            }
        } catch (error) {
            const statusTag = document.getElementById('status-tag');
            statusTag.textContent = '离线';
            statusTag.className = 'status-tag status-offline';
        }
    }

    initApp();
}); 