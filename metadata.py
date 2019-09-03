import os
import sys
import csv

class metaData():
    def __init__(self, fname):
        """initialising meta"""
        self.dict = {}
        self.name = fname
        self.loadData()

    def loadData(self):
        f = open(self.name, 'r')
        lines = f.read().splitlines()
        tableOpened = False
        tableName = ''
        for line in lines:
            if tableOpened:
                tableName = line
                tableOpened = False
                self.dict[tableName] = []

            elif "<begin_table>" in line:
                tableOpened = True
            
            elif "<end_table>" in line:
                tableOpened = False
            
            else:
                self.dict[tableName].append(line)

    def printData(self):
        print(self.dict)
    