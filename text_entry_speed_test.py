#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
import re
import pandas as pd
from io import StringIO
import time

from PyQt5.QtWidgets import QPushButton, QGridLayout


class SuperText(QtWidgets.QTextEdit):
 
    def __init__(self, example_text):
        super(SuperText, self).__init__()
        self.numbers=[]
        self.template_doc = ""
        self.setHtml(example_text)
        self.prev_content = ""
        self.prev_word = ""
        self.prev_sentence = ""
        self.sentence_index = 0
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
            content = re.sub(" " + str(numbers[num_id])  , " <a href='%d'>$%d$</a>" % (num_id, num_id), content, count=1)
        self.template_doc = content


    def text_changed(self):
        print("key pressed at: ", time.time(), end=", ")
        if len(self.prev_content) < len(self.toPlainText()):
            current_letter = self.toPlainText()[-1]
            if current_letter in [" ", ",", ".", "?"]:
                if len(self.toPlainText()) >= 2:
                    if not self.toPlainText()[-2] in [" ", ",", ".", "?"]:
                        self.prev_word = re.findall(r"[\w']+", self.prev_content)[-1]
                        print("word typed at", time.time(), ":", self.prev_word)
            if current_letter in ["\n"]:
                self.prev_sentence = self.prev_content.split("\n")[-1]
                print("sentence typed at", time.time(), ": ", self.prev_sentence)
        self.prev_content = self.toPlainText()


    def setup_table(self):
        # Initializes test & dataframe
        self.column_names = ["sentence index", "Timestamp (start)", "Timestamp (end)", "word typed", "entry speed", "Time mm:ss", "Timestamp (test finished)"]
        self.log_data = pd.DataFrame(columns=self.column_names)
        self.log_data[self.column_names[1]] = ["Hi", "There"]

        # https://stackoverflow.com/questions/51201519/pandas-to-csvsys-stdout-doesnt-work-under-my-environment/51201718
        output = StringIO()
        self.log_data.to_csv(output)
        output.seek(0)
        print(output.read())

    def closeEvent(self, event):
        print("Closes")


def main():
    app = QtWidgets.QApplication(sys.argv)
    super_text = SuperText("")
    sys.exit(app.exec_())



if __name__ == '__main__':
    main()
