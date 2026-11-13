import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import main


class TagsDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        main.DATA_DIR = self.root
        main.THUMB_DIR = self.root / "thumbnails"
        self.path = self.root / "media_notes.db"

    def make_file(self, name="one.jpg"):
        path = self.root / name
        path.write_bytes(b"picture")
        return path

    def test_multiple_tags_and_and_filter(self):
        db = main.Database(self.path)
        self.addCleanup(db.conn.close)
        a = db.add_category("A")
        b = db.add_category("B")
        c = db.add_category("C")
        path = self.make_file()
        self.assertTrue(db.add_media(str(path), "image", [a, b]))
        media_id = int(db.media_items()[0]["id"])
        self.assertEqual(set(db.tags_for_media(media_id)), {a, b})
        self.assertEqual(len(db.media_items([a])), 1)
        self.assertEqual(len(db.media_items([b])), 1)
        self.assertEqual(len(db.media_items([a, b])), 1)
        self.assertEqual(len(db.media_items([a, c])), 0)
        self.assertEqual(len(db.media_items([db.default_category_id()])), 0)

        db.add_media_tags([media_id], [c])
        self.assertEqual(set(db.tags_for_media(media_id)), {a, b, c})
        db.remove_media_tags([media_id], [a])
        self.assertEqual(set(db.tags_for_media(media_id)), {b, c})
        db.replace_media_tags([media_id], [])
        self.assertEqual(db.tags_for_media(media_id), [])
        self.assertEqual(len(db.media_items([db.default_category_id()])), 1)

    def test_updating_one_media_preserves_other_tags(self):
        db = main.Database(self.path)
        self.addCleanup(db.conn.close)
        a = db.add_category("A")
        b = db.add_category("B")
        db.add_media(str(self.make_file()), "image", [a])
        media_id = int(db.media_items()[0]["id"])
        db.update_media(media_id, "My name", "Some note", [a, b], 3)
        row = db.media_by_id(media_id)
        self.assertEqual(row["caption"], "My name")
        self.assertEqual(row["notes"], "Some note")
        self.assertEqual(row["rating"], 3)
        self.assertEqual(set(db.tags_for_media(media_id)), {a, b})
        db.delete_category(a)
        self.assertEqual(db.tags_for_media(media_id), [b])
        self.assertEqual(int(db.media_by_id(media_id)["category_id"]), b)
        self.assertEqual(len(db.media_items([b], "B")), 1)

    def test_ctrl_click_filters_intersection_in_window(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        from PySide6.QtWidgets import QApplication

        db = main.Database(self.path)
        self.addCleanup(db.conn.close)
        a = db.add_category("Tag A")
        b = db.add_category("Tag B")
        db.add_media(str(self.make_file("one.jpg")), "image", [a, b])
        db.add_media(str(self.make_file("two.jpg")), "image", [a])
        main.DB_PATH = self.path
        app = QApplication.instance() or QApplication([])
        window = main.MainWindow()
        self.addCleanup(window.close)
        window.show()
        app.processEvents()

        def click_tag(tag_id, modifiers):
            for index in range(window.category_list.count()):
                item = window.category_list.item(index)
                if item.data(Qt.UserRole) == tag_id:
                    pos = window.category_list.visualItemRect(item).center()
                    QTest.mouseClick(
                        window.category_list.viewport(),
                        Qt.LeftButton,
                        modifiers,
                        pos=pos,
                    )
                    app.processEvents()
                    return
            self.fail(f"Missing tag {tag_id}")

        click_tag(a, Qt.NoModifier)
        self.assertEqual(window.selected_category_ids(), [a])
        self.assertEqual(window.media_list.count(), 2)
        click_tag(b, Qt.ControlModifier)
        self.assertEqual(set(window.selected_category_ids()), {a, b})
        self.assertEqual(window.media_list.count(), 1)
        click_tag(b, Qt.NoModifier)
        self.assertEqual(window.selected_category_ids(), [b])
        self.assertEqual(window.media_list.count(), 1)

    def test_picker_stays_open_and_sorts_by_number_of_media(self):
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtTest import QTest
        from PySide6.QtWidgets import QApplication, QCheckBox

        db = main.Database(self.path)
        self.addCleanup(db.conn.close)
        popular = db.add_category("Oblíbený")
        common = db.add_category("Běžný")
        rare = db.add_category("Vzácný")
        db.add_media(str(self.make_file("first.jpg")), "image", [popular])
        db.add_media(str(self.make_file("second.jpg")), "image", [popular, common])
        db.add_media(str(self.make_file("third.jpg")), "image", [popular, common])
        main.DB_PATH = self.path

        app = QApplication.instance() or QApplication([])
        window = main.MainWindow()
        self.addCleanup(window.close)
        self.addCleanup(window.db.conn.close)
        window.show()
        app.processEvents()

        menu = window.detail_tags_menu
        widgets = [
            action.defaultWidget() for action in menu.actions()
            if action.defaultWidget() is not None
        ]
        self.assertTrue(all(isinstance(w, QCheckBox) for w in widgets))
        self.assertEqual(
            [w.text() for w in widgets],
            ["Oblíbený  ·  3", "Běžný  ·  2", "Vzácný  ·  0"],
        )
        self.assertEqual(window.current_media_id, int(db.media_items()[0]["id"]))
        menu.popup(QPoint(150, 100))
        app.processEvents()
        self.assertTrue(menu.isVisible())

        # Click several checkboxes WITHOUT closing/reopening the menu.
        QTest.mouseClick(widgets[2], Qt.LeftButton)
        app.processEvents()
        self.assertTrue(menu.isVisible())
        self.assertIn(rare, window.selected_detail_tag_ids)
        QTest.mouseClick(widgets[1], Qt.LeftButton)
        app.processEvents()
        self.assertTrue(menu.isVisible())
        self.assertNotIn(common, window.selected_detail_tag_ids)

        menu.hide()
        window.save_current()
        self.assertEqual(set(db.tags_for_media(window.current_media_id)), {popular, rare})

    def test_create_five_tags_at_once_and_skip_duplicates(self):
        db = main.Database(self.path)
        self.addCleanup(db.conn.close)
        db.add_category("Původní")
        created, duplicates = db.add_categories_batch([
            "  Jeden  ", "Dva", "Tři", "Čtyři", "Pět",
            "jeden", "PŮVODNÍ", "", "   ",
        ])
        self.assertEqual(len(created), 5)
        self.assertEqual(duplicates, ["jeden", "PŮVODNÍ"])
        rows = db.categories()
        names = [row["name"] for row in rows if row["parent_id"] is None]
        self.assertEqual(
            names[-5:], ["Jeden", "Dva", "Tři", "Čtyři", "Pět"],
        )
        self.assertEqual(
            len({str(row["name"]).casefold() for row in rows}), len(rows)
        )

    def test_create_multiple_subtags_at_once(self):
        db = main.Database(self.path)
        self.addCleanup(db.conn.close)
        parent = db.add_category("Rodič")
        created, duplicates = db.add_categories_batch(
            ["Podtag 1", "Podtag 2", "Podtag 3"], parent
        )
        self.assertEqual(len(created), 3)
        self.assertEqual(duplicates, [])
        self.assertEqual(
            [db.category_by_id(tag_id)["parent_id"] for tag_id in created],
            [parent, parent, parent],
        )
        with self.assertRaisesRegex(ValueError, "jednu úroveň"):
            db.add_categories_batch(["Nepovolený"], created[0])
        self.assertFalse(
            any(row["name"] == "Nepovolený" for row in db.categories())
        )

    def test_multiline_dialog_creates_tags_in_one_action(self):
        from unittest.mock import patch
        from PySide6.QtWidgets import QApplication

        main.DB_PATH = self.path
        app = QApplication.instance() or QApplication([])
        window = main.MainWindow()
        self.addCleanup(window.close)
        self.addCleanup(window.db.conn.close)

        with patch.object(
            main.QInputDialog,
            "getMultiLineText",
            return_value=("A\\nB\\nC\\nD\\nE", True),
        ) as dialog:
            window.add_category()
            dialog.assert_called_once()
        names = {row["name"] for row in window.db.categories()}
        self.assertTrue({"A", "B", "C", "D", "E"}.issubset(names))
        parent = next(
            int(row["id"]) for row in window.db.categories()
            if row["name"] == "A"
        )
        with patch.object(
            main.QInputDialog,
            "getMultiLineText",
            return_value=("Pod 1\\nPod 2", True),
        ) as dialog:
            window.add_subcategory(parent_id=parent)
            dialog.assert_called_once()
        children = [
            row["name"] for row in window.db.categories()
            if row["parent_id"] == parent
        ]
        self.assertEqual(children, ["Pod 1", "Pod 2"])

    def test_legacy_category_migration_and_backup(self):
        with sqlite3.connect(self.path) as conn:
            conn.executescript("""
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    parent_id INTEGER
                );
                CREATE TABLE media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    caption TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    rating INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    file_device INTEGER, file_inode INTEGER, file_size INTEGER,
                    fingerprint TEXT
                );
                INSERT INTO categories(id, name) VALUES (1, 'Nezařazené');
                INSERT INTO categories(id, name) VALUES (2, 'Původní tag');
                INSERT INTO media(id, path, media_type, category_id)
                VALUES (1, '/tmp/old.gif', 'gif', 2);
            """)
        db = main.Database(self.path)
        self.addCleanup(db.conn.close)
        self.assertEqual(db.tags_for_media(1), [2])
        self.assertTrue((self.root / "media_notes.before_tags.db").exists())
        self.assertEqual(len(db.media_items([2])), 1)
        db2 = main.Database(self.path)
        self.addCleanup(db2.conn.close)
        self.assertEqual(db2.tags_for_media(1), [2])


if __name__ == "__main__":
    unittest.main()
