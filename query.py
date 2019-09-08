
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
        self.where = False
        self.wclause = []
        self.andop = False
        self.orop = False
        self.tables = []
        self.pagg = []
        
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
                # print('ghusa')
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
            
            if self.tables == [] or not self.validate_tables():
                print('tables could not be validated')
                exit(0)


            if self.all:
                for tab in self.tables:
                    if tab in self.meta.dict:
                        for col in self.meta.dict[tab]:
                            self.cols.append(tab+'.'+col)

            if ind < len(query.tokens) and type(query.tokens[ind]).__name__ == 'Where':
                self.where = True
                self.wclause = [token for token in (query.tokens[ind]).tokens]            
                for token in self.wclause:
                    if str(token).upper() == 'AND':
                        self.andop = True
                    elif str(token).upper() == 'OR':
                        self.orop = True

            

            self.parse_aggregate()
            
            if not self.validate_cols():   
                print('columns could not be validated')
                exit(0)
            # print('sdfghuasdhjkfsdjkfhgs')
            # self.parse_aggregate()
            
            self.join_tables()
            # print(self.nt)
            self.show_distinct()
            self.show_where()
            # print(self.nt)
            self.aggregate_func()
            if self.aggregate:
                self.cols = self.pagg
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
                self.pagg.append(self.aggfn[-1]+'('+self.make_col(self.aggcols[-1])[0]+')')
        if self.aggregate:
            self.cols = self.aggcols

    def validate_query(self, query):
        if str(query.tokens[0]).upper() != 'SELECT':
            return False 
        if len(query.tokens) < 7:
            print('invalid query')
            exit(0)
        # if 'from' not in query.tokens and 'FROM' not in query.tokens:
        #     print('query should have from')
        #     exit(0)
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
            cnt = 0
            ret = ''
            check = False
            for table in self.tables:
                if table in self.meta.dict:
                    if col in self.meta.dict[table]:
                        cnt += 1
                        ret = table+'.'+col
                        check = True 
                        # return table+'.'+col, True
            if cnt == 1:
                return ret, check
            elif cnt > 1:
                print('ambiguous column')
                exit(0)
                return ret, False
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

    def wapply(self, row):
        check = True
        for token in self.wclause:
            ident1 = None
            op = None
            ident2 = None
            val = None
            ret = True
            if type(token).__name__ == 'Comparison':    
                for t in token.tokens:
                    if type(t).__name__ == 'Identifier':
                        if ident1 is None:
                            ident1,_ = self.make_col(str(t))
                        else:
                            ident2,_ = self.make_col(str(t))
                    elif str(t.ttype) == 'Token.Operator.Comparison':
                        op = str(t)
                    elif str(t.ttype) == 'Token.Literal.Number.Integer':
                        val = int(str(t))
                if ident1 is not None and ident2 is not None:
                    if ident2 in self.cols:
                        splt1 = ident1.split('.')
                        splt2 = ident2.split('.')
                        if op == '=' and splt1[0] != splt2[0] and self.all:
                            self.cols.remove(ident2)
                    ret = self.applyop(int(row[ident1]), int(row[ident2]), op)
                elif ident1 is not None and val is not None:
                    ret = self.applyop(int(row[ident1]), val, op)

                if self.andop:
                    check = check and ret
                elif self.orop:
                    check = check or ret
                else:
                    check = ret
        return row, check
    
    def applyop(self, val1, val2, op):
        if op == '=':
            return (val1 == val2)

        if op == '<':
            return (val1 < val2)

        if op == '<=':
            return (val1 <= val2)

        if op == '>=':
            return (val1 >= val2)

        if op == '>':
            return (val1 > val2)

    def show_where(self):
        newTab = []
        if self.where:
            for row in self.nt:
                trow, check = self.wapply(row)
                if check:
                    newTab.append(trow)
            self.nt = newTab     

    def show_distinct(self):
        distinct = []
        newTab = []
        if self.distinct:
            for row in self.nt:
                fields = [row[col] for col in self.cols]
                fields = [str(x) for x in fields]
                if fields not in distinct:
                    distinct.append(fields)
                    newTab.append(row)
            self.nt = newTab  

    def aggregate_func(self):
  
        sum_result = {}
        max_result = {}
        min_result = {}
        for d in self.nt:
            for k in d.keys():
                sum_result[k] = sum_result.get(k,0) + d[k]
                max_result[k] = max(max_result.get(k,float('-inf')), d[k])
                min_result[k] = min(min_result.get(k,float('inf')), d[k])
        # print(sum_result, max_result, min_result)
        if len(self.aggfn) > 0:
            for i in range(len(self.aggfn)):
                col,_ = self.make_col(self.aggcols[i])
                fname = self.aggfn[i] + '(' + col + ')'
                for row in self.nt:
                    if self.aggfn[i].upper() == 'SUM':
                        row[fname] = sum_result[col]
                    if self.aggfn[i].upper() == 'MIN':
                        row[fname] = min_result[col]
                    if self.aggfn[i].upper() == 'MAX':
                        row[fname] = max_result[col]
                    if self.aggfn[i].upper() == 'AVG' or self.aggfn[i].upper() == 'AVERAGE':
                        row[fname] = sum_result[col]/len(self.nt)
            # print(self.nt)
            # print(self.cols)
            if len(self.nt) > 1:
                self.nt = [self.nt[0]]
            # self.cols = cols


    def print_result(self):
        # print('+++',self.cols)
        writer = csv.DictWriter(sys.stdout, self.cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(self.nt)