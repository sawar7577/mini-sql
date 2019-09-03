import os
import sys
import sqlparse
import copy
import csv

class Query:

    def __init__(self, meta, tables):
        self.meta = meta
        self.all = False
        self.distinct = False
        self.aggregate = False
        self.tablesDict = tables
        self.aggfn = []
        self.aggcols = []
        self.cols = []
        
    def process(self, command):
        query = sqlparse.parse(command.strip(''))[0]

        if self.validate_query(query) == False:
            print('invalid query')
        
        else:
            ind = 2
            
            if str(query.tokens[ind].ttype) ==  'Token.Wildcard':
                if str(query.tokens[ind]) == '*':
                    self.all = True
                    ind += 2
                
            if str(query.tokens[ind]).upper() == 'DISTINCT':
                self.distinct = True
                ind += 2
                    
            if type(query.tokens[ind]).__name__ == 'IdentifierList':
                self.cols = [col for col in list(query.tokens[ind].get_identifiers())]
                ind += 2

            elif type(query.tokens[ind]).__name__ == 'Function':
                self.cols = [query.tokens[ind]]                
                self.aggregate = True
                ind += 2

            elif type(query.tokens[ind]).__name__ == 'Identifier':
                self.cols = [query.tokens[ind]]
                ind += 2

            if str(query.tokens[ind]).upper() == 'FROM':
                ind += 2
            else:
                pass 

            if type(query.tokens[ind]).__name__ == 'IdentifierList':
                self.tables = [str(table) for table in list(query.tokens[ind].get_identifiers())]
                ind += 2

            elif type(query.tokens[ind]).__name__ == 'Identifier':
                self.tables = [str(query.tokens[ind])]
                ind += 2
            
            if self.all:
                for tab in self.tables:
                    if tab in self.meta.dict:
                        for col in self.meta.dict[tab]:
                            self.cols.append(tab+'.'+col)

            self.parse_aggregate()

            if self.validate_cols():
                pass
            else:   
                print('columns could not be validated')


            self.join_tables()
            self.aggregate_func()
            self.print_result()

    def parse_aggregate(self):
        
        for i,col in enumerate(self.cols):
            if type(col).__name__ == 'Function':
                self.aggregate = True
                for token in col.tokens:
                    if type(token).__name__ == 'Identifier':
                        self.aggfn.append(str(token).upper())
                    else:
                        self.aggcols.append(str(token).strip('(').strip(')'))
        if self.aggregate:
            self.cols = self.aggcols

    def validate_query(self, query):
        if str(query.tokens[0]).upper() != 'SELECT':
            return False 
        return True

    def validate_tables(self):
        for table in self.tables:
            if table not in self.meta.dict:
                print('invalid table', table)
                return False
        return True

        

    def validate_cols(self):
        self.cols = [str(col) for col in self.cols]

        for ind in range(len(self.cols)):
            self.cols[ind], check = self.make_col(self.cols[ind])
            if not check:
                return False
        
        return True

    def make_col(self, col):
        if '.' in col:
            tab = col.split('.')[0]
            attrib = col.split('.')[1]
            check = False
            for table in self.tables:
                if table in self.meta.dict:
                    if attrib in self.meta.dict[table]:
                        check = True
            return col, check
        else:
            for table in self.tables:
                if table in self.meta.dict:
                    if col in self.meta.dict[table]:
                        return table+'.'+col, True
            return col, False
    

    def join_tables(self):
        nts = []
        for row in self.tablesDict[self.tables[0]].list:
            rts = {}
            for col in row:
                rts[self.tables[0] + '.' + col] = row[col]
            nts.append(rts)
        for i in range(1,len(self.tables)):
            temp  = []
            for row in self.tablesDict[self.tables[i]].list:
                for row2 in nts:
                    rts = copy.deepcopy(row2)
                    for col in row:
                        rts[self.tables[i]+'.'+col] = row[col]
                    temp.append(rts)
            nts = temp
        self.nt = nts        


    def aggregate_func(self):
  
        sum_result = {}
        max_result = {}
        min_result = {}
        for d in self.nt:
            for k in d.keys():
                sum_result[k] = sum_result.get(k,0) + d[k]
                max_result[k] = max(max_result.get(k,float('-inf')), d[k])
                min_result[k] = min(min_result.get(k,float('inf')), d[k])

        print(sum_result, max_result, min_result)

        


    def print_result(self):
        writer = csv.DictWriter(sys.stdout, self.cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(self.nt)