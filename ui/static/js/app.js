// Video Gia Dung Studio - Client JS Application

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCharacterUpload();
    initProductUpload();
    initOutputsTab();
    fetchSystemStatus();
    loadProductsList();
    loadOutputsList();

    // Global refresh button
    document.getElementById('btnRefresh').addEventListener('click', () => {
        fetchSystemStatus();
        loadProductsList();
        loadOutputsList();
        showToast('Đã làm mới dữ liệu!', 'info');
    });
});

// Toast notification helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// -------------------------------------------------------------
// TAB NAVIGATION
// -------------------------------------------------------------
function initTabs() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    const titles = {
        'tab-character': {
            title: 'Quản Lý Nhân Vật Mẫu',
            sub: 'Đảm bảo tính đồng nhất 100% gương mặt và thần thái nhân vật qua mọi video'
        },
        'tab-product-upload': {
            title: 'Tải Lên Sản Phẩm Mới',
            sub: 'Cung cấp hình ảnh và đặc tính sản phẩm để AI Agent phân tích tạo kịch bản chuyên biệt'
        },
        'tab-products-list': {
            title: 'Kho Dữ Liệu Sản Phẩm',
            sub: 'Danh sách các sản phẩm gia dụng đã tiếp nhận trong hệ thống'
        },
        'tab-outputs': {
            title: 'Kho Video & Ảnh Duyệt',
            sub: 'Xem lại các phân cảnh video 9:16 và ảnh mẫu xưởng / kho / cận cảnh đã sinh'
        },
        'tab-guidelines': {
            title: 'Quy Chuẩn AI Agent & TikTok Shop',
            sub: 'Quy định từ cấm, chính sách giá và 9 nguyên tắc cốt lõi khi sản xuất video'
        }
    };

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            navButtons.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const activePane = document.getElementById(targetTab);
            if (activePane) activePane.classList.add('active');

            if (titles[targetTab]) {
                document.getElementById('pageTitle').textContent = titles[targetTab].title;
                document.getElementById('pageSubtitle').textContent = titles[targetTab].sub;
            }

            if (targetTab === 'tab-products-list') loadProductsList();
            if (targetTab === 'tab-outputs') loadOutputsList();
        });
    });
}

// -------------------------------------------------------------
// SYSTEM STATUS & ACTIVE CHARACTER
// -------------------------------------------------------------
async function fetchSystemStatus() {
    try {
        const res = await fetch('/api/system/status');
        const data = await res.json();

        // Update stats pills
        document.getElementById('statProdCount').textContent = data.stats.products_count;
        document.getElementById('statVideoCount').textContent = data.stats.outputs_videos;
        document.getElementById('countProductsNav').textContent = data.stats.products_count;

        // Update character images
        if (data.character_info.portrait_url) {
            const cacheBuster = `?t=${Date.now()}`;
            document.getElementById('sidebarCharImg').src = data.character_info.portrait_url + cacheBuster;
            document.getElementById('activePortraitImg').src = data.character_info.portrait_url + cacheBuster;
        }

        // Render character history
        renderCharacterHistory(data.character_info.files || []);
    } catch (err) {
        console.error('Error fetching system status:', err);
    }
}

function renderCharacterHistory(files) {
    const grid = document.getElementById('charHistoryGrid');
    if (!files.length) {
        grid.innerHTML = '<div style="font-size:12px; color:var(--text-sub);">Chưa có ảnh nào khác</div>';
        return;
    }

    grid.innerHTML = files.map(file => `
        <div class="char-thumb-item ${file.is_active ? 'active' : ''}" title="${file.filename} (${file.size_kb} KB)" onclick="setActiveCharacter('${file.filename}')">
            <img src="${file.url}?t=${Date.now()}" alt="${file.filename}">
        </div>
    `).join('');
}

async function setActiveCharacter(filename) {
    try {
        const formData = new FormData();
        formData.append('filename', filename);

        const res = await fetch('/api/character/set-active', {
            method: 'POST',
            body: formData
        });
        const result = await res.json();
        if (res.ok) {
            showToast(result.message, 'success');
            fetchSystemStatus();
        } else {
            showToast(result.detail || 'Lỗi khi kích hoạt ảnh', 'error');
        }
    } catch (err) {
        showToast('Lỗi kết nối máy chủ', 'error');
    }
}

// -------------------------------------------------------------
// CHARACTER UPLOAD MANAGEMENT
// -------------------------------------------------------------
function initCharacterUpload() {
    const dropZone = document.getElementById('charDropZone');
    const fileInput = document.getElementById('charFileInput');
    const previewContainer = document.getElementById('charFilePreview');
    const dropContent = dropZone.querySelector('.drop-zone-content');
    const tempImg = document.getElementById('charTempImg');
    const fileNameSpan = document.getElementById('charFileName');
    const btnRemove = document.getElementById('btnRemoveCharFile');
    const btnUpload = document.getElementById('btnUploadChar');
    const form = document.getElementById('charUploadForm');

    let selectedFile = null;

    dropZone.addEventListener('click', (e) => {
        if (!e.target.closest('#btnRemoveCharFile')) {
            fileInput.click();
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length) {
            handleCharFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleCharFile(fileInput.files[0]);
        }
    });

    function handleCharFile(file) {
        if (!file.type.startsWith('image/')) {
            showToast('Chỉ chấp nhận file hình ảnh (PNG, JPG, WEBP)', 'error');
            return;
        }
        selectedFile = file;
        fileNameSpan.textContent = file.name;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            tempImg.src = e.target.result;
            dropContent.classList.add('hidden');
            previewContainer.classList.remove('hidden');
            btnUpload.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    btnRemove.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = '';
        dropContent.classList.remove('hidden');
        previewContainer.classList.add('hidden');
        btnUpload.disabled = true;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        btnUpload.disabled = true;
        btnUpload.innerHTML = '<span>Đang tải lên...</span>';

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('set_as_default', document.getElementById('chkSetDefaultChar').checked);

        try {
            const res = await fetch('/api/character/upload', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();
            if (res.ok) {
                showToast(result.message, 'success');
                btnRemove.click();
                fetchSystemStatus();
            } else {
                showToast(result.detail || 'Lỗi tải ảnh', 'error');
            }
        } catch (err) {
            showToast('Lỗi kết nối máy chủ', 'error');
        } finally {
            btnUpload.disabled = false;
            btnUpload.innerHTML = '<span>Lưu Nhân Vật Mẫu</span>';
        }
    });
}

// -------------------------------------------------------------
// PRODUCT UPLOAD MANAGEMENT
// -------------------------------------------------------------
let productFiles = [];

function initProductUpload() {
    const dropZone = document.getElementById('prodDropZone');
    const fileInput = document.getElementById('prodFilesInput');
    const previewGrid = document.getElementById('prodPreviewGrid');
    const form = document.getElementById('productForm');
    const btnSubmit = document.getElementById('btnSubmitProd');

    dropZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length) {
            addProdFiles(Array.from(e.dataTransfer.files));
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            addProdFiles(Array.from(fileInput.files));
        }
    });

    function addProdFiles(files) {
        files.forEach(f => {
            if (f.type.startsWith('image/')) {
                productFiles.push(f);
            }
        });
        renderProdPreviews();
    }

    function renderProdPreviews() {
        previewGrid.innerHTML = '';
        productFiles.forEach((file, idx) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const box = document.createElement('div');
                box.className = 'preview-thumb-box';
                box.innerHTML = `
                    <img src="${e.target.result}" alt="${file.name}">
                    <button type="button" class="btn-remove" style="position:absolute; top:2px; right:2px; background:rgba(0,0,0,0.6); padding:2px 6px; font-size:14px; border-radius:4px;" onclick="removeProdFile(${idx})">×</button>
                `;
                previewGrid.appendChild(box);
            };
            reader.readAsDataURL(file);
        });
    }

    window.removeProdFile = function(idx) {
        productFiles.splice(idx, 1);
        renderProdPreviews();
    };

    document.getElementById('btnResetProdForm').addEventListener('click', () => {
        productFiles = [];
        previewGrid.innerHTML = '';
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!productFiles.length) {
            showToast('Vui lòng tải lên ít nhất 1 ảnh sản phẩm!', 'error');
            return;
        }

        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<span>Đang lưu sản phẩm...</span>';

        const formData = new FormData();
        formData.append('name', document.getElementById('prodName').value);
        formData.append('category', document.getElementById('prodCategory').value);
        formData.append('scale_desc', document.getElementById('prodScale').value);
        formData.append('key_features', document.getElementById('prodFeatures').value);
        formData.append('pain_points', document.getElementById('prodPainPoints').value);
        formData.append('target_audience', document.getElementById('prodAudience').value);
        formData.append('notes', document.getElementById('prodNotes').value);

        productFiles.forEach(file => {
            formData.append('images', file);
        });

        try {
            const res = await fetch('/api/products/create', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();
            if (res.ok) {
                showToast(result.message, 'success');
                form.reset();
                productFiles = [];
                previewGrid.innerHTML = '';
                fetchSystemStatus();
                // Switch to products tab
                document.querySelector('.nav-btn[data-tab="tab-products-list"]').click();
            } else {
                showToast(result.detail || 'Lỗi khi lưu sản phẩm', 'error');
            }
        } catch (err) {
            showToast('Lỗi kết nối máy chủ', 'error');
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                    <polyline points="7 3 7 8 15 8"></polyline>
                </svg>
                <span>Lưu Sản Phẩm Vào Hệ Thống</span>
            `;
        }
    });
}

// -------------------------------------------------------------
// PRODUCTS CATALOG LIST
// -------------------------------------------------------------
let cachedProducts = [];

async function loadProductsList() {
    const container = document.getElementById('productsCatalogGrid');
    try {
        const res = await fetch('/api/products/list');
        const data = await res.json();
        cachedProducts = data.products || [];
        renderProductsCatalog(cachedProducts);
    } catch (err) {
        container.innerHTML = '<div style="color:var(--danger)">Lỗi khi tải danh sách sản phẩm.</div>';
    }
}

function renderProductsCatalog(products) {
    const container = document.getElementById('productsCatalogGrid');
    if (!products.length) {
        container.innerHTML = '<div class="empty-state" style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-sub);">Chưa có sản phẩm nào được lưu. Hãy bấm "Tải Sản Phẩm Mới" để thêm sản phẩm đầu tiên!</div>';
        return;
    }

    container.innerHTML = products.map(p => `
        <div class="product-card">
            <div class="prod-card-media">
                <img src="${p.primary_image || (p.images && p.images[0] ? p.images[0].url : '/static/img/placeholder.png')}" alt="${p.product_name}">
            </div>
            <div class="prod-card-body">
                <span class="prod-badge">${p.category || 'Đồ gia dụng'}</span>
                <h4>${p.product_name}</h4>
                <div class="prod-card-meta">
                    <div>📏 <strong>Kích thước:</strong> ${p.scale_description || 'Chuẩn đời thực'}</div>
                    <div>🎯 <strong>Đối tượng:</strong> ${p.target_audience || 'Gia đình'}</div>
                </div>
                <div class="prod-card-actions">
                    <span style="font-size:11px; color:var(--text-sub);">${p.created_at || ''}</span>
                    <button class="btn-del" onclick="deleteProduct('${p.product_id}')">Xoá</button>
                </div>
            </div>
        </div>
    `).join('');
}

// Search filter
document.getElementById('searchProdInput')?.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = cachedProducts.filter(p => 
        p.product_name.toLowerCase().includes(q) || 
        (p.category && p.category.toLowerCase().includes(q))
    );
    renderProductsCatalog(filtered);
});

async function deleteProduct(productId) {
    if (!confirm('Bạn có chắc chắn muốn xoá sản phẩm này?')) return;
    try {
        const res = await fetch(`/api/products/${productId}`, { method: 'DELETE' });
        const result = await res.json();
        if (res.ok) {
            showToast(result.message, 'success');
            loadProductsList();
            fetchSystemStatus();
        }
    } catch (err) {
        showToast('Lỗi khi xoá sản phẩm', 'error');
    }
}

// -------------------------------------------------------------
// OUTPUTS GALLERY (VIDEOS & IMAGES)
// -------------------------------------------------------------
function initOutputsTab() {
    const subtabs = document.querySelectorAll('.subtab-btn');
    const subContents = document.querySelectorAll('.subtab-content');

    subtabs.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.subtab;
            subtabs.forEach(b => b.classList.remove('active'));
            subContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(target).classList.add('active');
        });
    });
}

async function loadOutputsList() {
    try {
        const res = await fetch('/api/outputs/list');
        const data = await res.json();

        document.getElementById('countVideosPill').textContent = data.videos.length;
        document.getElementById('countImagesPill').textContent = data.images.length;

        renderVideosGallery(data.videos);
        renderImagesGallery(data.images);
    } catch (err) {
        console.error('Error loading outputs:', err);
    }
}

function renderVideosGallery(videos) {
    const grid = document.getElementById('videosGalleryGrid');
    if (!videos.length) {
        grid.innerHTML = '<div class="empty-state" style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-sub);">Chưa có video render nào trong thư mục outputs/</div>';
        return;
    }

    grid.innerHTML = videos.map(v => `
        <div class="video-card">
            <div class="video-player-wrap">
                <video controls playsinline preload="metadata">
                    <source src="${v.url}" type="video/mp4">
                    Trình duyệt không hỗ trợ xem video.
                </video>
            </div>
            <div class="video-info">
                <div>
                    <div class="name">${v.filename}</div>
                    <div class="meta">${v.size_mb} MB • ${v.created_at}</div>
                </div>
                <a href="${v.url}" download="${v.filename}" class="btn btn-secondary" style="padding:4px 10px; font-size:12px;">Tải MP4</a>
            </div>
        </div>
    `).join('');
}

function renderImagesGallery(images) {
    const grid = document.getElementById('imagesGalleryGrid');
    if (!images.length) {
        grid.innerHTML = '<div class="empty-state" style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-sub);">Chưa có ảnh duyệt nào trong thư mục outputs/</div>';
        return;
    }

    grid.innerHTML = images.map(img => `
        <div class="product-card">
            <div class="prod-card-media" style="height:320px;">
                <img src="${img.url}" alt="${img.filename}">
            </div>
            <div class="prod-card-body" style="padding:10px 14px;">
                <div class="name" style="font-size:12.5px; font-weight:600; color:#fff;">${img.filename}</div>
                <div class="meta" style="font-size:11px; color:var(--text-muted);">${img.size_mb} MB • ${img.created_at}</div>
            </div>
        </div>
    `).join('');
}
