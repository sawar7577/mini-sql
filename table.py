import os
import sys
import csv

class Table():

    def __init__(self, fname, meta):
        self.name = fname
        self.list = []
        self.meta = meta

        self.loadTable()
        # self.printTable()

    def loadTable(self):
        f = open('./files/'+self.name+'.csv', 'r')
        csvf = csv.reader(f)
        for row in csvf:
            rd = {}
            for i in range(len(row)):

                col_name = self.meta.dict[self.name][i]
                rd[col_name] = int(row[i])
            self.list.append(rd)

    def printTable(self):
        for row in self.list:
            print(row)