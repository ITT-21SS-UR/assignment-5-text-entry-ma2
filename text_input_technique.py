#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

from PyQt5 import QtGui, QtCore, QtWidgets
import re
import pandas as pd
from io import StringIO
import time
from datetime import date
import csv

pd.set_option("display.max_rows", None, "display.max_columns", None)


class SuperText(QtWidgets.QTextEdit):

    def __init__(self, example_text):
        super(SuperText, self).__init__()
        self.numbers = []
        self.template_doc = ""
        self.setHtml(example_text)
        self.prev_content = ""
        self.prev_word = ""
        self.prev_sentence = ""
        self.sentence_index = 0
        self.test_start_time = time.time()
        self.last_word_timestamp = 0
        # Additions:
        self.input_technique_enabled = input_technique_enabled
        self.ignore_text_changes = False
        self.placeholder_dict = [None, None]
        self.get_placeholder()
        # ....till here
        self.generate_template()
        self.render_template()
        self.initUI()
        self.setup_table()

    def initUI(self):
        self.setGeometry(0, 0, 400, 400)
        self.setWindowTitle('SuperText')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.textChanged.connect(lambda: self.text_changed())
        self.prev_content = self.toPlainText()
        self.show()

    def wheelEvent(self, ev):
        super(SuperText, self).wheelEvent(ev)
        self.generate_template()
        self.render_template()
        anc = self.anchorAt(ev.pos())
        if (anc):
            self.change_value(anc, ev.angleDelta().y())

    def change_value(self, val_id, amount):
        self.numbers[int(str(val_id))] += amount / 120
        self.render_template()

    def render_template(self):
        cur = self.textCursor()
        doc = self.template_doc
        for num_id, num in enumerate(self.numbers):
            doc = doc.replace('$' + str(num_id) + '$', '%d' % (num))
        self.setHtml(doc)
        self.setTextCursor(cur)

    def generate_template(self):
        content = str(self.toPlainText())
        numbers = list(re.finditer(" -?[0-9]+", content))
        numbers = [int(n.group()) for n in numbers]
        self.numbers = numbers
        if len(numbers) == 0:
            self.template_doc = content
            return
        for num_id in range(len(numbers)):
            content = re.sub(" " + str(numbers[num_id]), " <a href='%d'>$%d$</a>" % (num_id, num_id), content, count=1)
        self.template_doc = content

    def text_changed(self):
        # registers text changes
        if self.last_word_timestamp == 0:
            # starting test at first keypress through setting test_start time
            self.test_start_time = time.time()
            self.last_word_timestamp = time.time()
        # needed Addition:
        if not self.ignore_text_changes:
            print("key pressed at", time.time(), end=", ")
            # prints any keypress outside of csv table -- 'cause saving these timestamp in csv would be a overkill
            if len(self.prev_content) < len(self.toPlainText()):
                # if there was anything added to the current content then:
                current_letter = self.toPlainText()[-1]
                if current_letter in [" ", ",", ".", "?", "!"]:
                    self.process_word()
                if current_letter in ["\n"]:
                    self.process_word()
                    self.prev_sentence = self.prev_content.split("\n")[-1]
                    print("sentence typed at", time.time(), ": ", self.prev_sentence)
                    self.sentence_finished_on_table()
            self.prev_content = self.toPlainText()
            # updates self.prev_content

    def process_word(self):
        if len(self.toPlainText()) >= 2:
            if not self.toPlainText()[-2] in [" ", ",", ".", "?", "\n"]:
                # tests if the last entry was a word/number
                self.prev_word = re.findall(r"[\w'/$]+", self.prev_content)[-1]
                print("word typed at", time.time(), ":", self.prev_word)
                self.add_word_to_table()

                if self.input_technique_enabled & (self.prev_word[0] == "$"):
                    self.check_for_placeholder(self.prev_word)

    """
        Additions:
    """

    def get_placeholder(self):
        # setup placeholder
        self.placeholder_dict = {
            "$DATE": date.today().strftime("%d.%m.%Y"),
            "$MFG": "Mit freundlichen Gr????en"
        }
        file = Path(filepath)
        # reads from file (optional) and adds to dictionary
        if file.is_file():
            with open(filepath, mode='r') as infile:
                reader = csv.reader(infile)
                for rows in reader:
                    self.placeholder_dict[rows[0]] = rows[1]
        print(self.placeholder_dict)

    def check_for_placeholder(self, word):
        # checks if key has placeholder
        replacement = self.placeholder_dict.get(word, "invalid")
        if replacement == "invalid":
            return
        self.ignore_text_changes = True
        self.setText(self.toPlainText().replace(word, replacement))
        self.ignore_text_changes = False
        self.moveCursor(QtGui.QTextCursor.End)

    """
        till here
    """

    def setup_table(self):
        # Initializes main dataframe
        self.column_names = ["sentence index", "Timestamp (start of word)", "Timestamp (end of word)", "word typed",
                             "entry speed (in ms)", "Timestamp (test started)", "Timestamp (test finished)"]
        self.log_data = pd.DataFrame(columns=self.column_names)

    def add_word_to_table(self):
        # adding a row:
        current_time = time.time()
        temp_df = pd.DataFrame(columns=self.column_names)
        temp_df["sentence index"] = [self.sentence_index]
        temp_df["Timestamp (start of word)"] = [int(self.last_word_timestamp * 1000)]
        temp_df["Timestamp (end of word)"] = [int(current_time) * 1000]
        temp_df["word typed"] = [self.prev_word]
        temp_df["entry speed (in ms)"] = [int((current_time - self.last_word_timestamp) * 1000)]
        temp_df["Timestamp (test started)"] = [int(self.test_start_time) * 1000]
        self.log_data = self.log_data.append(temp_df, ignore_index=True)

    def sentence_finished_on_table(self):
        print()
        self.sentence_index = self.sentence_index + 1
        self.log_table()
        return

    def log_table(self):
        # https://stackoverflow.com/questions/51201519/pandas-to-csvsys-stdout-doesnt-work-under-my-environment/51201718
        # --> method to convert dataframe to csv and to write it in stdout
        output = StringIO()
        self.log_data.to_csv(output)
        output.seek(0)
        print(output.read())

    def closeEvent(self, event):
        current_time = time.time()
        print("\n\ntest finished (all sentences typed) at", current_time)
        self.log_data["Timestamp (test finished)"] = int(current_time * 1000)
        self.log_table()
        print("Closes")


def main():
    # Additions - technique activates on stdin:
    global filepath, input_technique_enabled
    filepath = ""
    input_technique_enabled = True
    input_technique_enabled = input("Enable input technique?(Y/N) : ").lower()[0] == "y"
    if input_technique_enabled:
        print("input technique enabled")
        filepath = input("Placeholder table path (optional) : ")
    else:
        print("input technique disabled")
    # ...till here
    app = QtWidgets.QApplication(sys.argv)
    super_text = SuperText("")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
