import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QMenu, QFileDialog, QMessageBox, QApplication, QProgressBar
)
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QAction, QFont

from .config import get_checked_sources, get_download_path, get_spin_limit, set_checked_sources, set_download_path, set_spin_limit

from .constants import (
    MUSICDL_AVAILABLE, SEARCH_SUCCESS_PROMPT, musicdl, SOURCE_MAP_CN_TO_EN, SOURCE_MAP_EN_TO_CN,MODERN_STYLE
)
from .utils import get_file_format, get_album_image_url
from .widgets import ModernSpinBox, FlowLayout, SimpleProgressDialog
from .workers import ImageDownloadTask, SearchThread, DownloadThread

class MusicDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 音乐下载器")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        font = QFont("Microsoft YaHei", 10)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        QApplication.setFont(font)
        self.setStyleSheet(MODERN_STYLE)

        # 数据
        self.search_results = {}
        self.music_records = {}
        self.music_client = None
        self.current_right_click_row = -1

        # 线程池
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(10)

        # 路径
        self.current_dir = os.getcwd()
        self.save_dir = os.path.join(os.getcwd(), get_download_path())
        os.makedirs(self.save_dir, exist_ok=True)

        self.auto_download_after_search = False

        # 界面搭建
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        self.setup_top(main_layout)
        self.setup_table(main_layout)

        if not MUSICDL_AVAILABLE:
            QMessageBox.warning(
                self, "警告", "musicdl 库未安装！\n请运行: pip install musicdl"
            )

    def setup_top(self, parent_layout):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 音乐源选择组
        group = QGroupBox("选择音乐源")
        flow = FlowLayout()
        self.source_checkboxes = []
        for cn_name in SOURCE_MAP_CN_TO_EN.keys():
            cb = QCheckBox(cn_name)
            if cn_name in get_checked_sources():
                cb.setChecked(True)
            self.source_checkboxes.append(cb)
            flow.addWidget(cb)
        group.setLayout(flow)
        layout.addWidget(group)

        # 数量、目录、自动下载
        h1 = QHBoxLayout()
        label_limit = QLabel("单源获取数量：")
        self.spin_limit = ModernSpinBox()
        self.spin_limit.setRange(1, 100)
        self.spin_limit.setValue(get_spin_limit())
        self.spin_limit.setSuffix(" 条")
        self.spin_limit.setFixedWidth(100)

        explanation_label = QLabel("(每个音乐源获取的歌曲数量)")
        explanation_label.setStyleSheet("color: #6b7280; font-size: 12px;")

        label_save = QLabel("保存目录：")
        self.save_dir_edit = QLineEdit(self.save_dir)
        self.save_dir_edit.setReadOnly(True)
        self.btn_browse = QPushButton("📁 浏览...")
        self.btn_browse.clicked.connect(self.on_browse_save_dir)

        self.check_auto_download = QCheckBox("🚀 搜索后自动下载全部")
        self.check_auto_download.setStyleSheet("font-weight: bold; color: #dc2626;")
        self.check_auto_download.stateChanged.connect(self.on_auto_download_toggle)

        h1.addWidget(label_limit)
        h1.addWidget(explanation_label)
        h1.addWidget(self.spin_limit)
        h1.addSpacing(15)
        h1.addWidget(label_save)
        h1.addWidget(self.save_dir_edit, 1)
        h1.addWidget(self.btn_browse)
        h1.addSpacing(15)
        h1.addWidget(self.check_auto_download)
        layout.addLayout(h1)

        # 搜索行
        h2 = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("请输入关键词或输入歌单链接，按回车键也可搜索...")
        self.search_edit.returnPressed.connect(self.on_search)

        self.btn_search = QPushButton("🔍 立即搜索")
        self.btn_search.setObjectName("SearchBtn")
        self.btn_search.setFixedWidth(110)
        self.btn_search.clicked.connect(self.on_search)

        h2.addWidget(self.search_edit)
        h2.addWidget(self.btn_search)
        layout.addLayout(h2)

        # 搜索进度条
        self.search_progress = QProgressBar()
        self.search_progress.setRange(0, 100)
        self.search_progress.setValue(0)
        self.search_progress.setVisible(False)
        self.search_progress.setStyleSheet("""
            QProgressBar { border: none; border-radius: 4px; background-color: #f3f4f6; height: 6px; }
            QProgressBar::chunk { background-color: #0078d4; border-radius: 4px; }
        """)
        layout.addWidget(self.search_progress)

        parent_layout.addLayout(layout)

    def setup_table(self, parent_layout):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 下载范围选择栏
        batch = QHBoxLayout()
        self.btn_download = QPushButton("⬇️ 下载选中内容")
        self.btn_download.clicked.connect(self.on_download)
        self.btn_download.setEnabled(False)

        batch.addStretch()
        batch.addWidget(self.btn_download)
        layout.addLayout(batch)

        # 表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(9)
        self.results_table.setHorizontalHeaderLabels(
            ["选择", "专辑封面", "歌曲名", "歌手", "专辑", "格式", "大小", "时长", "来源"]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setShowGrid(False)
        self.results_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_table_context_menu)
        # 启用排序功能（除了第0列选择框和第1列封面）
        self.results_table.horizontalHeader().setSectionsClickable(True)
        self.results_table.setSortingEnabled(True)
        # 连接排序信号
        self.results_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        self.results_table.setColumnWidth(0, 40)
        self.results_table.setColumnWidth(1, 65)
        self.results_table.setColumnWidth(2, 280)
        self.results_table.setColumnWidth(3, 160)
        self.results_table.setColumnWidth(4, 200)
        self.results_table.setColumnWidth(5, 60)
        self.results_table.setColumnWidth(6, 80)
        self.results_table.setColumnWidth(7, 70)
        self.results_table.verticalHeader().setDefaultSectionSize(54)

        layout.addWidget(self.results_table)
        parent_layout.addLayout(layout)

    # ---------- 槽函数 ----------
    def on_auto_download_toggle(self, state):
        self.auto_download_after_search = (state == Qt.CheckState.Checked)

    def on_browse_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存/导出目录", self.current_dir)
        if dir_path:
            self.save_dir = dir_path
            self.save_dir_edit.setText(dir_path)
            set_download_path(dir_path)

    def show_table_context_menu(self, pos):
        item = self.results_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        self.current_right_click_row = row

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: white; border: 1px solid #e5e7eb; border-radius: 6px; } "
            "QMenu::item { padding: 4px 20px; color: #374151; } "
            "QMenu::item:selected { background-color: #0078d4; color: white; }"
        )

        song_name_item = self.results_table.item(row, 2)
        singer_item = self.results_table.item(row, 3)
        action_text = (
            f"📥 下载：{song_name_item.text()} - {singer_item.text()}"
            if (song_name_item and singer_item)
            else "📥 下载此歌曲"
        )

        download_action = QAction(action_text, self)
        download_action.triggered.connect(self.download_current_row)
        menu.addAction(download_action)
        menu.addSeparator()

        select_all_action = QAction("☑️ 全选所有歌曲", self)
        select_all_action.triggered.connect(self.select_all_songs)
        menu.addAction(select_all_action)

        deselect_all_action = QAction("🔲 取消全选", self)
        deselect_all_action.triggered.connect(self.deselect_all_songs)
        menu.addAction(deselect_all_action)

        menu.exec(self.results_table.mapToGlobal(pos))

    def download_current_row(self):
        if self.current_right_click_row < 0 or not self.music_client:
            return
        row_key = str(self.current_right_click_row)
        if row_key not in self.music_records:
            return
        song_info = self.music_records[row_key]
        song_name = song_info.get("song_name", "未知歌曲")
        singers = ", ".join(song_info.get("singers", []))

        reply = QMessageBox.question(
            self,
            "确认下载",
            f"确定要下载这首歌曲吗？\n\n🎵 {song_name} - {singers}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._start_download_task([song_info], f"正在处理：{song_name}")

    def select_all_songs(self):
        for row in range(self.results_table.rowCount()):
            cell_widget = self.results_table.cellWidget(row, 0)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)

    def deselect_all_songs(self):
        for row in range(self.results_table.rowCount()):
            cell_widget = self.results_table.cellWidget(row, 0)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)

    def on_header_clicked(self, logical_index):
        # 不允许对选择列和封面列排序
        if logical_index in (0, 1):
            # 取消排序状态
            self.results_table.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
            return

    # ---------- 核心功能 ----------
    def init_music_client(self):
        if not MUSICDL_AVAILABLE:
            return None
        os.makedirs(self.save_dir, exist_ok=True)
        temp_work_dir = os.path.join(self.current_dir, ".musicdl_temp")
        os.makedirs(temp_work_dir, exist_ok=True)

        src_names = self.get_selected_sources()
        if not src_names:
            QMessageBox.warning(self, "提示", "请至少选择一个音乐来源！")
            return None

        cfg = {
            src: {
                "search_size_per_source": self.spin_limit.value(),
                "work_dir": temp_work_dir,
            }
            for src in src_names
        }
        try:
            if musicdl:
                return musicdl.MusicClient(
                    music_sources=src_names, init_music_clients_cfg=cfg
                )
            return None
        except Exception as e:
            QMessageBox.critical(self, "错误", f"初始化 musicdl 客户端失败：{str(e)}")
            return None

    def get_selected_sources(self):
        return [
            SOURCE_MAP_CN_TO_EN[cb.text()]
            for cb in self.source_checkboxes
            if cb.isChecked()
        ]

    def load_table_with_results(self, search_results):
        # 获取当前的排序状态
        header = self.results_table.horizontalHeader()
        sort_column = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()

        self.results_table.setRowCount(0)
        self.search_results = search_results
        self.music_records = {}
        self.thread_pool.clear()

        all_songs = []
        for per_source in search_results.values():
            all_songs.extend(per_source)

        self.results_table.setRowCount(len(all_songs))
        row = 0
        for _, per_source_search_results in search_results.items():
            for per_source_search_result in per_source_search_results:
                # 选择框
                w = QWidget()
                lay = QHBoxLayout(w)
                lay.addWidget(QCheckBox())
                lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lay.setContentsMargins(0, 0, 0, 0)
                self.results_table.setCellWidget(row, 0, w)

                song_name = per_source_search_result.get("song_name", "")
                singers = per_source_search_result.get("singers", "")
                album = per_source_search_result.get("album", "")
                source_cn = SOURCE_MAP_EN_TO_CN.get(
                    per_source_search_result.get("source", ""), ""
                )

                items = [
                    "",  # 选择框占位
                    "",  # 封面占位
                    str(song_name),
                    str(singers),
                    str(album),
                    get_file_format(per_source_search_result),
                    str(per_source_search_result.get("file_size", "")),
                    str(per_source_search_result.get("duration", "")),
                    str(source_cn),
                ]

                for column, text in enumerate(items):
                    if column in (0, 1):
                        continue
                    table_item = QTableWidgetItem(text)
                    align = (
                        Qt.AlignmentFlag.AlignLeft
                        if column in (2, 3, 4)
                        else Qt.AlignmentFlag.AlignHCenter
                    )
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | align)
                    self.results_table.setItem(row, column, table_item)

                self.music_records[str(row)] = per_source_search_result

                # 异步下载封面
                album_image_url = get_album_image_url(per_source_search_result)
                if album_image_url:
                    task = ImageDownloadTask(row, album_image_url)
                    task.signals.finished.connect(self.on_image_downloaded)
                    task.signals.error.connect(self.on_image_error)
                    self.thread_pool.start(task)
                else:
                    self.on_image_error(row)

                row += 1

        self.btn_download.setEnabled(row > 0)

        # 恢复排序状态（如果之前有排序）
        if sort_column > 1:  # 跳过选择列和封面列
            self.results_table.sortItems(sort_column, sort_order)

        if self.auto_download_after_search and all_songs:
            self._start_download_task(all_songs, f"正在处理 {len(all_songs)} 首歌曲")
        else:
            if SEARCH_SUCCESS_PROMPT:
                QMessageBox.information(
                    self,
                    "搜索完毕",
                    f"🎉 搜索完成！共找到 {row} 首歌曲。\n(专辑封面正在后台加载...)",
                )

    def on_image_downloaded(self, row, pixmap):
        try:
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("border-radius: 3px;")
            self.results_table.setCellWidget(row, 1, label)
        except Exception as e:
            print(f"设置专辑封面失败: {e}")

    def on_image_error(self, row):
        try:
            label = QLabel("🎵")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 20px; color: #d1d5db;")
            self.results_table.setCellWidget(row, 1, label)
        except Exception as e:
            print(f"设置专辑封面失败: {e}")

    def get_songs_by_download_scope(self):
        # 现在只下载勾选的歌曲
        songs = []
        for row in range(self.results_table.rowCount()):
            cell_widget = self.results_table.cellWidget(row, 0)
            if not cell_widget:
                continue
            checkbox = cell_widget.findChild(QCheckBox)
            is_checked = checkbox.isChecked() if checkbox else False
            if is_checked:
                if str(row) in self.music_records:
                    songs.append(self.music_records[str(row)])
        return songs

    def _start_download_task(self, songs_list, msg):
        # 创建下载进度条（如果需要可以显示，目前保持隐藏）
        dlg = SimpleProgressDialog("下载提取中", msg, self.save_dir, self)
        dlg.show()

        self.download_thread = DownloadThread(self.music_client, songs_list, self.save_dir)

        def on_finished(success_count):
            dlg.accept()
            QMessageBox.information(
                self,
                "下载完成",
                f"✅ 成功提取 {success_count} 首歌曲！\n已保存在：{self.save_dir}",
            )

        def on_error(error_msg):
            dlg.accept()
            QMessageBox.critical(self, "错误", f"❌ 下载失败：{error_msg}")

        self.download_thread.finished.connect(on_finished)
        self.download_thread.error.connect(on_error)
        self.download_thread.start()

    def on_search(self):
        keyword = self.search_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入你要搜索的关键词！")
            return

        self.music_client = self.init_music_client()
        if not self.music_client:
            return

        self.btn_search.setEnabled(False)
        self.btn_search.setText("搜索中...")
        self.search_progress.setValue(0)
        self.search_progress.setVisible(True)

        self.search_thread = SearchThread(
            self.music_client, keyword, "搜索歌曲"
        )

        def on_finished(results):
            self.search_progress.setVisible(False)
            self.btn_search.setEnabled(True)
            self.btn_search.setText("🔍 立即搜索")
            self.load_table_with_results(results)

        def on_error(error_msg):
            self.search_progress.setVisible(False)
            self.btn_search.setEnabled(True)
            self.btn_search.setText("🔍 立即搜索")
            QMessageBox.critical(self, "错误", f"搜索失败：{error_msg}")

        def on_progress(progress_value):
            self.search_progress.setValue(progress_value)

        self.search_thread.finished.connect(on_finished)
        self.search_thread.error.connect(on_error)
        self.search_thread.progress.connect(on_progress)  # 连接进度信号
        self.search_thread.start()

    def on_download(self):
        if not self.music_client:
            return
        songs_to_download = self.get_songs_by_download_scope()
        if not songs_to_download:
            QMessageBox.warning(self, "提示", "没有符合条件的歌曲，请检查是否已勾选！")
            return

        reply = QMessageBox.question(
            self,
            "确认下载",
            f"确定要下载选中的 {len(songs_to_download)} 首歌曲吗？\n保存目录：{self.save_dir}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._start_download_task(
                songs_to_download,
                f"正在批量下载 {len(songs_to_download)} 首歌曲..."
            )
    def closeEvent(self, event):
        path = []
        set_spin_limit(self.spin_limit.value())
        for cb in self.source_checkboxes:
            if cb.isChecked():
                path.append(cb.text())
        set_checked_sources(path)
        event.accept()   
        