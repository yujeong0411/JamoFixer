# -*- coding: utf-8 -*-
"""
한글 파일명 자소 교정기 (NFD → NFC)
맥에서 보낸 파일명이 윈도우에서 'ㅍㅏㅇㅣㄹ'처럼 자모 분리되어 보일 때,
폴더를 선택하거나 끌어다 놓으면 정상 파일명으로 일괄 교정합니다.

작성: 최유정
"""

import json
import os
import sys
import unicodedata
import urllib.request

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QCheckBox,
    QFileDialog, QMessageBox, QHeaderView, QAbstractItemView, QFrame
)


__version__ = "1.0.0"
GITHUB_REPO = "yujeong0411/JamoFixer"


def resource_path(name: str) -> str:
    """개발 실행과 PyInstaller --onefile 실행 모두에서 리소스 경로를 돌려준다."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


class UpdateChecker(QThread):
    """GitHub Releases에서 최신 버전을 조회해 더 높은 게 있으면 신호를 보낸다.
    네트워크 오류·레이트 리밋 등은 조용히 무시(앱 동작에 영향 없음).
    """
    update_available = pyqtSignal(str, str)  # latest_version, html_url

    def run(self):
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "JamoFixer",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.load(resp)
        except Exception:
            return
        latest = (data.get("tag_name") or "").lstrip("v").strip()
        html_url = data.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases/latest"
        if latest and self._is_newer(latest, __version__):
            self.update_available.emit(latest, html_url)

    @staticmethod
    def _is_newer(latest: str, current: str) -> bool:
        try:
            def parse(v):
                return tuple(int(x) for x in v.split("."))
            return parse(latest) > parse(current)
        except Exception:
            return False


# ----------------------------- 핵심 로직 -----------------------------

def needs_fix(name: str) -> bool:
    """NFC로 정규화했을 때 이름이 달라지면 교정이 필요한 것."""
    return name != unicodedata.normalize("NFC", name)


def scan_folder(root: str, recursive: bool):
    """
    교정 대상 목록을 만든다.
    반환: [(전체경로, 현재이름, 바뀔이름, 종류('파일'/'폴더')), ...]
    폴더는 경로가 긴 것(=더 깊은 것)부터 처리해야 안전하므로 정렬해서 돌려준다.
    """
    files = []
    dirs = []

    if recursive:
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if needs_fix(fn):
                    files.append((os.path.join(dirpath, fn), fn,
                                  unicodedata.normalize("NFC", fn), "파일"))
            for dn in dirnames:
                if needs_fix(dn):
                    dirs.append((os.path.join(dirpath, dn), dn,
                                 unicodedata.normalize("NFC", dn), "폴더"))
    else:
        for entry in os.listdir(root):
            full = os.path.join(root, entry)
            if not needs_fix(entry):
                continue
            if os.path.isdir(full):
                dirs.append((full, entry, unicodedata.normalize("NFC", entry), "폴더"))
            else:
                files.append((full, entry, unicodedata.normalize("NFC", entry), "파일"))

    # 폴더는 깊은 것(경로 긴 것)부터 이름을 바꿔야 상위 경로가 꼬이지 않는다.
    dirs.sort(key=lambda x: len(x[0]), reverse=True)
    # 파일을 먼저, 폴더를 나중에.
    return files + dirs


def scan_folders(roots, recursive: bool):
    """여러 폴더를 한 번에 스캔해 합친다. 같은 항목은 중복 제거."""
    files = []
    dirs = []
    seen = set()
    for root in roots:
        try:
            entries = scan_folder(root, recursive)
        except OSError:
            continue
        for full, old, new, kind in entries:
            key = os.path.normcase(full)
            if key in seen:
                continue
            seen.add(key)
            if kind == "파일":
                files.append((full, old, new, kind))
            else:
                dirs.append((full, old, new, kind))
    dirs.sort(key=lambda x: len(x[0]), reverse=True)
    return files + dirs


def apply_fix(items):
    """
    실제 이름 변경 수행.
    반환: (성공 수, [(현재이름, 사유) ...] 건너뛴 목록)
    """
    ok = 0
    skipped = []
    for full, old, new, kind in items:
        parent = os.path.dirname(full)
        target = os.path.join(parent, new)
        # 대상 이름이 이미 다른 파일로 존재하면 덮어쓰지 않고 건너뜀
        if os.path.exists(target) and os.path.normcase(target) != os.path.normcase(full):
            skipped.append((old, "같은 이름이 이미 있어 건너뜀"))
            continue
        try:
            os.rename(full, target)
            ok += 1
        except OSError as e:
            skipped.append((old, f"오류: {e.strerror or e}"))
    return ok, skipped


# ----------------------------- GUI -----------------------------

class JamoFixer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.folder_roots = []
        self.file_paths = []
        self.items = []
        self.setWindowTitle("Jamo Fixer")
        self.setMinimumSize(720, 560)
        self.setAcceptDrops(True)
        self._build_ui()
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._show_update_banner)
        self._update_checker.start()

    def _show_update_banner(self, latest: str, url: str):
        self.update_banner.setText(
            f'🔔 새 버전 <b>{latest}</b> 사용 가능 '
            f'(현재 {__version__}) — '
            f'<a href="{url}">다운로드 페이지 열기</a>'
        )
        self.update_banner.setVisible(True)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        # 헤더
        title = QLabel("Jamo Fixer")
        title.setFont(QFont("맑은 고딕", 16, QFont.Weight.Bold))
        root.addWidget(title)

        sub = QLabel("맥에서 받은 파일명이 'ㅍㅏㅇㅣㄹ'처럼 분리되어 보일 때, "
                     "폴더를 고르거나 창에 끌어다 놓으면 정상 이름으로 고쳐줍니다.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#666;")
        root.addWidget(sub)

        self.update_banner = QLabel()
        self.update_banner.setOpenExternalLinks(True)
        self.update_banner.setStyleSheet(
            "background:#FFF8E1; color:#856404; padding:8px 12px;"
            "border:1px solid #FFE082; border-radius:6px;")
        self.update_banner.setVisible(False)
        root.addWidget(self.update_banner)

        # 드롭존 / 폴더 선택 줄
        top = QHBoxLayout()
        self.drop = QLabel("📂  여기로 폴더나 파일(여러 개 가능)을 끌어다 놓거나, 오른쪽 버튼으로 선택하세요")
        self.drop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop.setFixedHeight(64)
        self.drop.setStyleSheet(
            "border:2px dashed #bbb; border-radius:10px; color:#888; background:#fafafa;")
        top.addWidget(self.drop, 1)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        pick_folder = QPushButton("폴더 선택…")
        pick_folder.clicked.connect(self.choose_folder)
        btn_col.addWidget(pick_folder)
        pick_files = QPushButton("파일 선택…")
        pick_files.clicked.connect(self.choose_files)
        btn_col.addWidget(pick_files)
        top.addLayout(btn_col)
        root.addLayout(top)

        # 옵션 줄
        opt = QHBoxLayout()
        self.recursive = QCheckBox("하위 폴더까지 포함")
        self.recursive.setChecked(True)
        self.recursive.stateChanged.connect(self.refresh_preview)
        opt.addWidget(self.recursive)
        opt.addStretch(1)
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color:#2E7D32; font-weight:bold;")
        opt.addWidget(self.count_label)
        self.clear_btn = QPushButton("초기화")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self.clear_roots)
        opt.addWidget(self.clear_btn)
        root.addLayout(opt)

        # 미리보기 표
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["종류", "현재 이름", "바뀔 이름"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        root.addWidget(self.table, 1)

        # 하단 버튼 줄
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#e0e0e0;")
        root.addWidget(line)

        bottom = QHBoxLayout()
        self.status = QLabel("폴더를 선택하면 미리보기가 표시됩니다.")
        self.status.setStyleSheet("color:#888;")
        bottom.addWidget(self.status, 1)

        self.fix_btn = QPushButton("변환하기")
        self.fix_btn.setFixedSize(140, 44)
        self.fix_btn.setEnabled(False)
        self.fix_btn.setStyleSheet(
            "QPushButton{background:#2E7D32;color:white;border:none;border-radius:8px;"
            "font-size:14px;font-weight:bold;}"
            "QPushButton:disabled{background:#cccccc;}"
            "QPushButton:hover:enabled{background:#27692b;}")
        self.fix_btn.clicked.connect(self.do_fix)
        bottom.addWidget(self.fix_btn)
        root.addLayout(bottom)

    # ---------- 드래그앤드롭 ----------
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.drop.setStyleSheet(
                "border:2px dashed #2E7D32; border-radius:10px; color:#2E7D32; background:#eef7ef;")

    def dragLeaveEvent(self, e):
        self.drop.setStyleSheet(
            "border:2px dashed #bbb; border-radius:10px; color:#888; background:#fafafa;")

    def dropEvent(self, e):
        self.dragLeaveEvent(e)
        urls = e.mimeData().urls()
        if not urls:
            return
        paths = [u.toLocalFile() for u in urls if u.toLocalFile()]
        if paths:
            self.add_sources(paths)

    # ---------- 동작 ----------
    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if path:
            self.add_sources([path])

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "파일 선택")
        if paths:
            self.add_sources(paths)

    def add_sources(self, paths):
        existing_folders = {os.path.normcase(os.path.abspath(p)) for p in self.folder_roots}
        existing_files = {os.path.normcase(os.path.abspath(p)) for p in self.file_paths}
        for p in paths:
            if not os.path.exists(p):
                continue
            key = os.path.normcase(os.path.abspath(p))
            if os.path.isdir(p):
                if key in existing_folders:
                    continue
                existing_folders.add(key)
                self.folder_roots.append(p)
            else:
                if key in existing_files:
                    continue
                existing_files.add(key)
                self.file_paths.append(p)
        self._update_drop_label()
        self.clear_btn.setEnabled(bool(self.folder_roots or self.file_paths))
        self.refresh_preview()

    def clear_roots(self):
        self.folder_roots = []
        self.file_paths = []
        self.items = []
        self.table.setRowCount(0)
        self.count_label.setText("")
        self.fix_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.drop.setText("📂  여기로 폴더나 파일(여러 개 가능)을 끌어다 놓거나, 오른쪽 버튼으로 선택하세요")
        self.drop.setStyleSheet(
            "border:2px dashed #bbb; border-radius:10px; color:#888; background:#fafafa;")
        self.status.setText("폴더를 선택하면 미리보기가 표시됩니다.")

    def _update_drop_label(self):
        nf, nfi = len(self.folder_roots), len(self.file_paths)
        if nf == 0 and nfi == 0:
            return
        parts = []
        if nf:
            parts.append(f"{nf}개 폴더")
        if nfi:
            parts.append(f"{nfi}개 파일")
        sample = self.folder_roots[0] if self.folder_roots else self.file_paths[0]
        if nf + nfi == 1:
            self.drop.setText("📂  " + sample)
        else:
            self.drop.setText(f"📂  {', '.join(parts)} — {sample} 외")
        self.drop.setStyleSheet(
            "border:2px solid #2E7D32; border-radius:10px; color:#2E7D32; background:#eef7ef;")

    def refresh_preview(self):
        if not self.folder_roots and not self.file_paths:
            return
        folder_items = scan_folders(self.folder_roots, self.recursive.isChecked())
        seen = {os.path.normcase(full) for full, *_ in folder_items}
        extra_files = []
        for fp in self.file_paths:
            if os.path.normcase(fp) in seen:
                continue
            name = os.path.basename(fp)
            if not needs_fix(name):
                continue
            extra_files.append((fp, name, unicodedata.normalize("NFC", name), "파일"))
        self.items = extra_files + folder_items

        self.table.setRowCount(len(self.items))
        for r, (full, old, new, kind) in enumerate(self.items):
            self.table.setItem(r, 0, QTableWidgetItem(kind))
            old_item = QTableWidgetItem(old)
            old_item.setForeground(QColor("#c0392b"))
            self.table.setItem(r, 1, old_item)
            new_item = QTableWidgetItem(new)
            new_item.setForeground(QColor("#2E7D32"))
            self.table.setItem(r, 2, new_item)

        n = len(self.items)
        self.count_label.setText(f"교정 대상 {n}개" if n else "교정할 항목 없음")
        self.fix_btn.setEnabled(n > 0)
        if n == 0:
            self.status.setText("이미 모두 정상입니다. 바꿀 파일이 없어요.")
        else:
            self.status.setText(f"{n}개 항목을 바꿀 수 있습니다. '변환하기'를 누르세요.")

    def do_fix(self):
        n = len(self.items)
        if n == 0:
            return
        reply = QMessageBox.question(
            self, "확인", f"{n}개 항목의 이름을 정상(NFC)으로 바꿉니다.\n계속할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok, skipped = apply_fix(self.items)
        msg = f"완료: {ok}개 변환됨"
        if skipped:
            msg += f"\n건너뜀: {len(skipped)}개"
            detail = "\n".join(f"· {name} — {why}" for name, why in skipped[:10])
            if len(skipped) > 10:
                detail += f"\n… 외 {len(skipped) - 10}개"
            box = QMessageBox(self)
            box.setWindowTitle("결과")
            box.setText(msg)
            box.setDetailedText(detail)
            box.exec()
        else:
            QMessageBox.information(self, "결과", msg)

        self.refresh_preview()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("맑은 고딕", 10))
    icon_path = resource_path("Icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    win = JamoFixer()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
