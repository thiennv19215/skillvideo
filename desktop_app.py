import sys
import os
import json
import shutil
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QScrollArea,
    QFrame, QGridLayout, QCheckBox, QSplitter, QStatusBar, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor, QPainter, QBrush, QPen, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QSize, pyqtSignal

# Base directories
BASE_DIR = Path(__file__).resolve().parent
MODELS_IMG_DIR = BASE_DIR / "models" / "images"
INPUTS_PROD_DIR = BASE_DIR / "inputs" / "products"
PRODUCTS_JSON_DIR = BASE_DIR / "products"
OUTPUTS_DIR = BASE_DIR / "outputs"

for d in [MODELS_IMG_DIR, INPUTS_PROD_DIR, PRODUCTS_JSON_DIR, OUTPUTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Dark Theme QSS
DARK_STYLESHEET = """
QMainWindow {
    background-color: #0b0f19;
}

QWidget {
    font-family: 'Segoe UI', 'Plus Jakarta Sans', Arial, sans-serif;
    color: #f1f5f9;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: #0f172a;
    border-radius: 12px;
    margin-top: -1px;
}

QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
}

QTabBar::tab:selected {
    background: #2563eb;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background: #334155;
    color: #ffffff;
}

QFrame.card {
    background-color: #131d31;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 16px;
}

QLabel {
    color: #f1f5f9;
}

QLabel.title {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
}

QLabel.subtitle {
    font-size: 12px;
    color: #94a3b8;
}

QLineEdit, QTextEdit, QComboBox {
    background-color: #0a0e17;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    selection-background-color: #2563eb;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
}

QPushButton {
    background: #1e293b;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #ffffff;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background: #334155;
}

QPushButton.primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
    border: none;
    padding: 10px 20px;
    color: #ffffff;
}

QPushButton.primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
}

QPushButton.success {
    background: #10b981;
    border: none;
    color: #ffffff;
}

QPushButton.success:hover {
    background: #059669;
}

QPushButton.danger {
    background: #ef4444;
    border: none;
    color: #ffffff;
}

QPushButton.danger:hover {
    background: #dc2626;
}

QListWidget {
    background-color: #0a0e17;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 8px;
}

QListWidget::item {
    background-color: #131d31;
    border-radius: 8px;
    margin-bottom: 6px;
    padding: 8px;
}

QListWidget::item:selected {
    background-color: #1e3a8a;
    border: 1px solid #3b82f6;
}

QScrollBar:vertical {
    border: none;
    background: #0b0f19;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}
"""

class DropImageLabel(QLabel):
    fileDropped = pyqtSignal(str)

    def __init__(self, placeholder_text="Kéo thả ảnh vào đây\nhoặc nhấp để chọn file"):
        super().__init__()
        self.placeholder_text = placeholder_text
        self.setText(self.placeholder_text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                background-color: rgba(255, 255, 255, 0.02);
                color: #94a3b8;
                font-weight: 500;
                font-size: 13px;
            }
            QLabel:hover {
                border-color: #3b82f6;
                background-color: rgba(59, 130, 246, 0.05);
                color: #ffffff;
            }
        """)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            filePath, _ = QFileDialog.getOpenFileName(
                self, "Chọn ảnh", "", "Image Files (*.png *.jpg *.jpeg *.webp)"
            )
            if filePath:
                self.fileDropped.emit(filePath)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            filePath = urls[0].toLocalFile()
            if filePath.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                self.fileDropped.emit(filePath)

class VideoStudioDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gia Dụng Studio AI - Ứng Dụng Desktop Quản Lý TikTok Shop")
        self.resize(1180, 760)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(DARK_STYLESHEET)
        
        self.selected_char_path = None
        self.selected_prod_images = []

        self.initUI()
        self.refreshCharacterDisplay()
        self.refreshProductsList()
        self.refreshOutputsList()

    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)
        mainLayout.setContentsMargins(16, 16, 16, 16)
        mainLayout.setSpacing(12)

        # Header Bar
        headerLayout = QHBoxLayout()
        titleLayout = QVBoxLayout()
        lblBrand = QLabel("🏠 GIA DỤNG STUDIO AI (DESKTOP)")
        lblBrand.setStyleSheet("font-size: 18px; font-weight: 800; color: #60a5fa;")
        lblSub = QLabel("Quản lý nhân vật mẫu đồng nhất 100% & tiếp nhận sản phẩm chuẩn TikTok Shop")
        lblSub.setStyleSheet("font-size: 12px; color: #94a3b8;")
        titleLayout.addWidget(lblBrand)
        titleLayout.addWidget(lblSub)
        headerLayout.addLayout(titleLayout)

        headerLayout.addStretch()

        btnRefreshAll = QPushButton("🔄 Làm Mới Dữ Liệu")
        btnRefreshAll.clicked.connect(self.refreshAll)
        headerLayout.addWidget(btnRefreshAll)

        mainLayout.addLayout(headerLayout)

        # Main Tabs
        self.tabs = QTabWidget()
        self.tabCharacter = self.createCharacterTab()
        self.tabProductUpload = self.createProductUploadTab()
        self.tabProductCatalog = self.createProductCatalogTab()
        self.tabOutputs = self.createOutputsTab()
        self.tabGuidelines = self.createGuidelinesTab()

        self.tabs.addTab(self.tabCharacter, "👤 Quản Lý Nhân Vật Mẫu")
        self.tabs.addTab(self.tabProductUpload, "📦 Tải Lên Sản Phẩm Mới")
        self.tabs.addTab(self.tabProductCatalog, "📂 Kho Sản Phẩm")
        self.tabs.addTab(self.tabOutputs, "🎬 Kho Video & Ảnh Duyệt")
        self.tabs.addTab(self.tabGuidelines, "📜 Quy Chuẩn AI Agent")

        mainLayout.addWidget(self.tabs)

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Sẵn sàng hoạt động | AI Agent End-to-End")

    def refreshAll(self):
        self.refreshCharacterDisplay()
        self.refreshProductsList()
        self.refreshOutputsList()
        self.statusBar.showMessage("Đã làm mới toàn bộ dữ liệu!", 3000)

    # -------------------------------------------------------------
    # TAB 1: CHARACTER MANAGEMENT
    # -------------------------------------------------------------
    def createCharacterTab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        # Left Column: Active Character Preview
        leftCard = QFrame()
        leftCard.setProperty("class", "card")
        leftLayout = QVBoxLayout(leftCard)

        lblTitle = QLabel("Chân Dung Nhân Vật Mẫu Hiện Tại")
        lblTitle.setProperty("class", "title")
        leftLayout.addWidget(lblTitle)

        self.lblActivePortrait = QLabel()
        self.lblActivePortrait.setFixedSize(240, 360)
        self.lblActivePortrait.setStyleSheet("""
            border: 2px solid #10b981;
            border-radius: 12px;
            background-color: #000;
        """)
        self.lblActivePortrait.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblActivePortrait.setScaledContents(True)
        leftLayout.addWidget(self.lblActivePortrait, alignment=Qt.AlignmentFlag.AlignCenter)

        lblInfo = QLabel(
            "<b>✓ Tỉ lệ chuẩn:</b> 9:16 Vertical<br>"
            "<b>✓ Nhận diện:</b> Nữ Á Đông 25-27t, tóc búi có mái rẽ ngôi<br>"
            "<b>✓ File cố định:</b> <code>models/images/character_portrait.png</code>"
        )
        lblInfo.setStyleSheet("font-size: 12px; color: #cbd5e1; margin-top: 8px;")
        leftLayout.addWidget(lblInfo)
        leftLayout.addStretch()

        layout.addWidget(leftCard, 1)

        # Right Column: Upload New Character
        rightCard = QFrame()
        rightCard.setProperty("class", "card")
        rightLayout = QVBoxLayout(rightCard)

        lblRightTitle = QLabel("Cập Nhật / Đổi Nhân Vật Mẫu Mới")
        lblRightTitle.setProperty("class", "title")
        rightLayout.addWidget(lblRightTitle)

        lblRightDesc = QLabel("Kéo thả file ảnh hoặc bấm để chọn ảnh từ máy tính (PNG, JPG, WEBP):")
        lblRightDesc.setProperty("class", "subtitle")
        rightLayout.addWidget(lblRightDesc)

        self.charDropZone = DropImageLabel("Kéo thả ảnh chân dung vào đây\nhoặc nhấp chuột để duyệt file...")
        self.charDropZone.setFixedHeight(160)
        self.charDropZone.fileDropped.connect(self.onCharacterFileSelected)
        rightLayout.addWidget(self.charDropZone)

        self.lblCharSelectedPath = QLabel("Chưa chọn file mới")
        self.lblCharSelectedPath.setStyleSheet("color: #94a3b8; font-size: 11px;")
        rightLayout.addWidget(self.lblCharSelectedPath)

        self.chkSetCharDefault = QCheckBox("Đặt làm nhân vật chuẩn mặc định ngay sau khi lưu")
        self.chkSetCharDefault.setChecked(True)
        rightLayout.addWidget(self.chkSetCharDefault)

        btnSaveChar = QPushButton("💾 Lưu Nhân Vật Mẫu")
        btnSaveChar.setProperty("class", "primary")
        btnSaveChar.clicked.connect(self.saveNewCharacter)
        rightLayout.addWidget(btnSaveChar)

        # History thumbnails
        lblHist = QLabel("Lịch Sử Các Ảnh Mẫu Đã Lưu (Nhấp đúp để kích hoạt lại):")
        lblHist.setStyleSheet("font-weight: 600; margin-top: 14px;")
        rightLayout.addWidget(lblHist)

        self.listCharHistory = QListWidget()
        self.listCharHistory.setIconSize(QSize(60, 90))
        self.listCharHistory.itemDoubleClicked.connect(self.activateHistoricalCharacter)
        rightLayout.addWidget(self.listCharHistory)

        layout.addWidget(rightCard, 2)
        return widget

    def onCharacterFileSelected(self, filePath):
        self.selected_char_path = filePath
        self.lblCharSelectedPath.setText(f"Đã chọn: {Path(filePath).name}")
        pixmap = QPixmap(filePath)
        if not pixmap.isNull():
            self.charDropZone.setPixmap(pixmap.scaled(self.charDropZone.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def saveNewCharacter(self):
        if not self.selected_char_path or not os.path.exists(self.selected_char_path):
            QMessageBox.warning(self, "Chưa chọn file", "Vui lòng chọn hoặc kéo thả ảnh nhân vật trước!")
            return

        try:
            suffix = Path(self.selected_char_path).suffix.lower()
            timestamp = int(time.time())
            backup_name = f"character_source_{timestamp}{suffix}"
            backup_path = MODELS_IMG_DIR / backup_name

            shutil.copyfile(self.selected_char_path, backup_path)

            if self.chkSetCharDefault.isChecked():
                target_path = MODELS_IMG_DIR / "character_portrait.png"
                shutil.copyfile(self.selected_char_path, target_path)

            QMessageBox.information(self, "Thành công", "Đã lưu ảnh nhân vật mẫu thành công!")
            self.selected_char_path = None
            self.charDropZone.setText("Kéo thả ảnh chân dung vào đây\nhoặc nhấp chuột để duyệt file...")
            self.lblCharSelectedPath.setText("Chưa chọn file mới")
            self.refreshCharacterDisplay()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {e}")

    def refreshCharacterDisplay(self):
        active_path = MODELS_IMG_DIR / "character_portrait.png"
        if active_path.exists():
            pixmap = QPixmap(str(active_path))
            self.lblActivePortrait.setPixmap(pixmap.scaled(240, 360, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else:
            self.lblActivePortrait.setText("Chưa có ảnh mẫu")

        # Refresh history list
        self.listCharHistory.clear()
        for f in MODELS_IMG_DIR.glob("*.*"):
            if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"] and f.name != "character_portrait.png":
                item = QListWidgetItem(f"{f.name} ({round(f.stat().st_size / 1024, 1)} KB)")
                item.setIcon(QIcon(str(f)))
                item.setData(Qt.ItemDataRole.UserRole, str(f))
                self.listCharHistory.addItem(item)

    def activateHistoricalCharacter(self, item):
        filePath = item.data(Qt.ItemDataRole.UserRole)
        if filePath and os.path.exists(filePath):
            reply = QMessageBox.question(
                self, "Xác nhận", f"Bạn có muốn đặt {Path(filePath).name} làm nhân vật mẫu chuẩn hiện tại?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                target_path = MODELS_IMG_DIR / "character_portrait.png"
                shutil.copyfile(filePath, target_path)
                self.refreshCharacterDisplay()
                self.statusBar.showMessage(f"Đã kích hoạt {Path(filePath).name} làm nhân vật mẫu chuẩn!", 3000)

    # -------------------------------------------------------------
    # TAB 2: PRODUCT UPLOAD & METADATA
    # -------------------------------------------------------------
    def createProductUploadTab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        # Left Column: Product Images
        leftCard = QFrame()
        leftCard.setProperty("class", "card")
        leftLayout = QVBoxLayout(leftCard)

        lblImgTitle = QLabel("Ảnh Sản Phẩm (Nhiều Góc Chụp)")
        lblImgTitle.setProperty("class", "title")
        leftLayout.addWidget(lblImgTitle)

        btnSelectProdImgs = QPushButton("➕ Chọn Một Hoặc Nhiều Ảnh Sản Phẩm")
        btnSelectProdImgs.clicked.connect(self.selectProductImages)
        leftLayout.addWidget(btnSelectProdImgs)

        self.listProdImages = QListWidget()
        self.listProdImages.setIconSize(QSize(70, 70))
        leftLayout.addWidget(self.listProdImages)

        btnClearImgs = QPushButton("🗑️ Xoá Toàn Bộ Ảnh Đã Chọn")
        btnClearImgs.clicked.connect(self.clearProductImages)
        leftLayout.addWidget(btnClearImgs)

        layout.addWidget(leftCard, 1)

        # Right Column: Product Intake Form
        rightCard = QFrame()
        rightCard.setProperty("class", "card")
        rightLayout = QVBoxLayout(rightCard)

        lblFormTitle = QLabel("Thông Tin Sản Phẩm & Kịch Bản AI")
        lblFormTitle.setProperty("class", "title")
        rightLayout.addWidget(lblFormTitle)

        # Form fields
        self.txtProdName = QLineEdit()
        self.txtProdName.setPlaceholderText("Ví dụ: Vỉ Dao Cạo Râu Gillette Vector Plus 1 Cán 4 Đầu Dao")
        rightLayout.addWidget(QLabel("<b>Tên Sản Phẩm *</b>"))
        rightLayout.addWidget(self.txtProdName)

        rowLayout = QHBoxLayout()
        self.cboCategory = QComboBox()
        self.cboCategory.addItems(["Đồ gia dụng & Nhà cửa", "Chăm sóc cá nhân & Làm đẹp", "Thiết bị nhà bếp", "Dụng cụ vệ sinh & Tiện ích", "Khác"])
        rowLayout.addWidget(QLabel("<b>Danh Mục:</b>"))
        rowLayout.addWidget(self.cboCategory)

        self.txtProdScale = QLineEdit()
        self.txtProdScale.setPlaceholderText("Ví dụ: Dài ~12cm cầm vừa vặn trong lòng bàn tay")
        rowLayout.addWidget(QLabel("<b>Kích Thước Thật:</b>"))
        rowLayout.addWidget(self.txtProdScale)
        rightLayout.addLayout(rowLayout)

        self.txtFeatures = QTextEdit()
        self.txtFeatures.setPlaceholderText("- 2 lưỡi dao kép sắc bén cạo sạch lướt êm\n- Đầu xoay chuyển động tự điều chỉnh ôm sát góc cạnh mặt\n- Dải gel bôi trơn dưa leo làm mát dịu da")
        self.txtFeatures.setFixedHeight(70)
        rightLayout.addWidget(QLabel("<b>Công Năng Vượt Trội (Mỗi dòng 1 ý)</b>"))
        rightLayout.addWidget(self.txtFeatures)

        self.txtPainPoints = QTextEdit()
        self.txtPainPoints.setPlaceholderText("- Dao thông thường cạo rát, dễ xước da, nhanh cùn\n- Mua lẻ ngoài tiệm đắt đỏ tốn kém")
        self.txtPainPoints.setFixedHeight(60)
        rightLayout.addWidget(QLabel("<b>Nỗi Đau Khách Hàng Cần Giải Quyết</b>"))
        rightLayout.addWidget(self.txtPainPoints)

        self.txtAudience = QLineEdit()
        self.txtAudience.setPlaceholderText("Ví dụ: Nam giới, người hay cạo râu hàng ngày, nhân viên văn phòng")
        rightLayout.addWidget(QLabel("<b>Đối Tượng Khách Hàng</b>"))
        rightLayout.addWidget(self.txtAudience)

        btnSaveProduct = QPushButton("💾 Lưu Sản Phẩm Vào Hệ Thống")
        btnSaveProduct.setProperty("class", "primary")
        btnSaveProduct.clicked.connect(self.saveProductData)
        rightLayout.addWidget(btnSaveProduct)

        layout.addWidget(rightCard, 2)
        return widget

    def selectProductImages(self):
        filePaths, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh sản phẩm", "", "Image Files (*.png *.jpg *.jpeg *.webp)"
        )
        for p in filePaths:
            if p not in self.selected_prod_images:
                self.selected_prod_images.append(p)
                item = QListWidgetItem(Path(p).name)
                item.setIcon(QIcon(p))
                self.listProdImages.addItem(item)

    def clearProductImages(self):
        self.selected_prod_images = []
        self.listProdImages.clear()

    def saveProductData(self):
        name = self.txtProdName.text().strip()
        if not name:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên sản phẩm!")
            return
        if not self.selected_prod_images:
            QMessageBox.warning(self, "Thiếu ảnh", "Vui lòng chọn ít nhất 1 ảnh sản phẩm!")
            return

        try:
            slug = "".join([c if c.isalnum() else "_" for c in name.lower()]).strip("_")
            timestamp = int(time.time())
            product_id = f"{slug}_{timestamp}" if slug else f"prod_{timestamp}"

            # Create product directory
            prod_dir = INPUTS_PROD_DIR / product_id
            prod_dir.mkdir(parents=True, exist_ok=True)

            saved_images = []
            for idx, img_path in enumerate(self.selected_prod_images):
                suffix = Path(img_path).suffix.lower()
                target_img_name = f"image_{idx+1}{suffix}"
                target_img_path = prod_dir / target_img_name
                shutil.copyfile(img_path, target_img_path)
                saved_images.append({
                    "filename": target_img_name,
                    "path": str(target_img_path.relative_to(BASE_DIR)).replace("\\", "/")
                })

            # Create json metadata
            features = [f.strip() for f in self.txtFeatures.toPlainText().split("\n") if f.strip()]
            pain_points = [p.strip() for p in self.txtPainPoints.toPlainText().split("\n") if p.strip()]

            product_data = {
                "product_id": product_id,
                "product_name": name,
                "category": self.cboCategory.currentText(),
                "scale_description": self.txtProdScale.text().strip() or "Kích thước tiêu chuẩn đời thực",
                "key_features": features,
                "pain_points": pain_points,
                "target_audience": self.txtAudience.text().strip() or "Khách hàng gia đình",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "images": saved_images,
                "primary_image": saved_images[0]["path"]
            }

            json_path = PRODUCTS_JSON_DIR / f"{product_id}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(product_data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "Thành công", f"Đã lưu sản phẩm '{name}' thành công!")
            
            # Reset form
            self.txtProdName.clear()
            self.txtProdScale.clear()
            self.txtFeatures.clear()
            self.txtPainPoints.clear()
            self.txtAudience.clear()
            self.clearProductImages()

            self.refreshProductsList()
            self.tabs.setCurrentIndex(2) # Switch to catalog tab
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu dữ liệu sản phẩm: {e}")

    # -------------------------------------------------------------
    # TAB 3: PRODUCTS CATALOG
    # -------------------------------------------------------------
    def createProductCatalogTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        topBar = QHBoxLayout()
        self.txtSearch = QLineEdit()
        self.txtSearch.setPlaceholderText("🔍 Tìm kiếm sản phẩm theo tên hoặc danh mục...")
        self.txtSearch.textChanged.connect(self.filterProductsList)
        topBar.addWidget(self.txtSearch)

        btnDeleteSelected = QPushButton("🗑️ Xoá Sản Phẩm Đã Chọn")
        btnDeleteSelected.setProperty("class", "danger")
        btnDeleteSelected.clicked.connect(self.deleteSelectedProduct)
        topBar.addWidget(btnDeleteSelected)

        layout.addLayout(topBar)

        self.listProductsCatalog = QListWidget()
        self.listProductsCatalog.setIconSize(QSize(100, 100))
        layout.addWidget(self.listProductsCatalog)

        return widget

    def refreshProductsList(self):
        self.listProductsCatalog.clear()
        for f in PRODUCTS_JSON_DIR.glob("*.json"):
            if f.name == "products_batch_template.json":
                continue
            try:
                with open(f, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    name = data.get("product_name", "Không rõ tên")
                    cat = data.get("category", "Gia dụng")
                    date = data.get("created_at", "")
                    primary_img = data.get("primary_image", "")
                    
                    item_text = f"📦 {name}\n📁 Danh mục: {cat} | 🕒 Ngày tạo: {date}\n📏 Kích thước: {data.get('scale_description', '')}"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, data.get("product_id"))
                    
                    img_full_path = BASE_DIR / primary_img if primary_img else None
                    if img_full_path and img_full_path.exists():
                        item.setIcon(QIcon(str(img_full_path)))

                    self.listProductsCatalog.addItem(item)
            except Exception:
                pass

    def filterProductsList(self, query):
        query = query.lower()
        for i in range(self.listProductsCatalog.count()):
            item = self.listProductsCatalog.item(i)
            item.setHidden(query not in item.text().lower())

    def deleteSelectedProduct(self):
        currItem = self.listProductsCatalog.currentItem()
        if not currItem:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn 1 sản phẩm trong danh sách để xoá!")
            return

        product_id = currItem.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Xác nhận xoá", f"Bạn có chắc muốn xoá dữ liệu sản phẩm {product_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            json_path = PRODUCTS_JSON_DIR / f"{product_id}.json"
            img_dir = INPUTS_PROD_DIR / product_id
            if json_path.exists():
                json_path.unlink()
            if img_dir.exists():
                shutil.rmtree(img_dir, ignore_errors=True)
            self.refreshProductsList()
            self.statusBar.showMessage("Đã xoá sản phẩm!", 3000)

    # -------------------------------------------------------------
    # TAB 4: OUTPUTS GALLERY (VIDEOS & APPROVED IMAGES)
    # -------------------------------------------------------------
    def createOutputsTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        topBar = QHBoxLayout()
        lbl = QLabel("Danh Sách Video & Ảnh Duyệt Thành Phẩm (Thư mục outputs/)")
        lbl.setProperty("class", "title")
        topBar.addWidget(lbl)

        topBar.addStretch()

        btnOpenOutputsFolder = QPushButton("📂 Mở Thư Mục outputs/ trong Windows")
        btnOpenOutputsFolder.clicked.connect(lambda: os.startfile(str(OUTPUTS_DIR)))
        topBar.addWidget(btnOpenOutputsFolder)

        layout.addLayout(topBar)

        self.listOutputs = QListWidget()
        self.listOutputs.setIconSize(QSize(80, 80))
        self.listOutputs.itemDoubleClicked.connect(self.openOutputFile)
        layout.addWidget(self.listOutputs)

        lblHint = QLabel("💡 Nhấp đúp chuột vào bất kỳ file nào để mở xem trực tiếp trên máy tính.")
        lblHint.setStyleSheet("color: #94a3b8; font-size: 11.5px;")
        layout.addWidget(lblHint)

        return widget

    def refreshOutputsList(self):
        self.listOutputs.clear()
        for f in sorted(OUTPUTS_DIR.glob("**/*.*"), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and f.suffix.lower() in [".mp4", ".png", ".jpg", ".webp"]:
                size_mb = round(f.stat().st_size / (1024 * 1024), 2)
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
                icon_type = "🎬 Video MP4" if f.suffix.lower() == ".mp4" else "🖼️ Ảnh duyệt 9:16"
                
                item = QListWidgetItem(f"{icon_type}: {f.name} ({size_mb} MB - {mtime})")
                item.setData(Qt.ItemDataRole.UserRole, str(f))
                if f.suffix.lower() in [".png", ".jpg", ".webp"]:
                    item.setIcon(QIcon(str(f)))
                self.listOutputs.addItem(item)

    def openOutputFile(self, item):
        filePath = item.data(Qt.ItemDataRole.UserRole)
        if filePath and os.path.exists(filePath):
            os.startfile(filePath)

    # -------------------------------------------------------------
    # TAB 5: AI AGENT GUIDELINES & POLICIES
    # -------------------------------------------------------------
    def createGuidelinesTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        card1 = QFrame()
        card1.setProperty("class", "card")
        c1Layout = QVBoxLayout(card1)
        c1Layout.addWidget(QLabel("<b>🎯 9 NGUYÊN TẮC CỐT LÕI AI AGENT (BẮT BUỘC 100%)</b>"))
        
        rulesText = (
            "1. <b>Đồng nhất nhân vật 100%:</b> Giữ nguyên ngũ quan và kiểu tóc từ models/images/character_portrait.png.<br>"
            "2. <b>Ảnh chụp thương mại chân thực:</b> Da có lỗ chân lông, ánh sáng thực. Tuyệt đối cấm vẽ 3D CGI hay hoạt hình.<br>"
            "3. <b>Chuẩn tỉ lệ đời thực:</b> Sản phẩm cầm trên tay vừa vặn đúng kích thước thực tế.<br>"
            "4. <b>Flow Provider MCP:</b> Upload lấy media_id trước khi sinh ảnh hoặc video Omni Flash.<br>"
            "5. <b>Lồng thoại tiếng Việt:</b> Nhúng trực tiếp câu thoại vào prompt video với nhép môi chân thực.<br>"
            "6. <b>Tránh nói về giá & từ cấm:</b> Không nhắc tiền cụ thể, tập trung vào công năng, nỗi đau và giải pháp.<br>"
            "7. <b>Quy trình 3 bước:</b> Soạn kịch bản ➔ 3 Option ảnh duyệt ➔ Render video và ghép nối MP4.<br>"
            "8. <b>Sáng tạo cá nhân hóa:</b> Không dập khuôn kịch bản, đổi mới liên tục theo đặc tính từng sản phẩm.<br>"
            "9. <b>Agent làm chủ toàn diện:</b> Tự động giám sát trực tiếp tiến độ render thời gian thực, không dựa dẫm script cứng nhắc."
        )
        lblRules = QLabel(rulesText)
        lblRules.setStyleSheet("line-height: 1.6; font-size: 13px; color: #e2e8f0;")
        c1Layout.addWidget(lblRules)
        layout.addWidget(card1)

        card2 = QFrame()
        card2.setProperty("class", "card")
        c2Layout = QVBoxLayout(card2)
        c2Layout.addWidget(QLabel("<b>⚠️ TỪ CẤM & CÂU KÊU GỌI CTA CHUẨN TIKTOK SHOP</b>"))
        
        policyText = (
            "• <b>Từ cấm tuyệt đối:</b> số 1, rẻ nhất, tốt nhất, cam kết 100%, vĩnh viễn, khỏi hoàn toàn, không lấy lợi nhuận.<br>"
            "• <b>Mẫu CTA hợp lệ:</b> <i>\"Bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết và nhận ưu đãi hôm nay.\"</i>"
        )
        lblPolicy = QLabel(policyText)
        lblPolicy.setStyleSheet("color: #fcd34d; font-size: 13px;")
        c2Layout.addWidget(lblPolicy)
        layout.addWidget(card2)

        layout.addStretch()
        return widget

def main():
    app = QApplication(sys.argv)
    window = VideoStudioDesktop()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
