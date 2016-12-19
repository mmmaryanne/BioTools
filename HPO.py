'''
hpo objects, including doing analyses such as hpo similarity, and group of hpos similarities
'''
import requests
import json
import os
import time
from CommonFuncs import *
from sqlite_utils import *

def _initiate_db(db_conn):
    db_c = db_conn.cursor()
    db_c.execute('''CREATE TABLE IF NOT EXISTS hpo
        (id text PRIMARY KEY UNIQUE, name text, parents text, ancestors text)''')
    db_conn.commit()

class Hpo:
    def __init__(self,id,db_conn):
        _initiate_db(db_conn)
        self.id = id
        self.db_conn = db_conn
    
    def _find_ancestors(self,id,anc,data):
        # construct_db helper function, to find all ancestors of a node
        is_a = data[id]['is_a']
        if not is_a:
            return anc
        else:
            anc.extend(is_a)
            for i in is_a:
                return self._find_ancestors(i,anc,data)
            
    def _check_db(self):
        # hpo has been constructed? if not, raise error. if yes, do nothing
        db_c = self.db_conn.cursor()
        db_c.execute('SELECT * FROM hpo WHERE id=?',('HP:0000001',))
        db_hpo = dict_factory(db_c,db_c.fetchone())
        if db_hpo == None:
            raise ValueError('No data seems to be in the hpo database. Did you forget to load it using HPO.construct_db("hp.obo")?')
    def construct_db(self,obofile):
        # construct hpo database using the obo file
        data = obo_parser(obofile)
        # get ancestors
        for k,v in data.iteritems():
            data[k]['ancestors'] = self._find_ancestors(k,[],data)
        
        # convert to array of tuples
        values = []
        for k,v in data.iteritems():
            values.append((
                k,
                v['name'],
                json.dumps(v['is_a'],indent=4),
                json.dumps(v['ancestors'],indent=4)
            ))
        # write to database
        db_c = self.db_conn.cursor()
        sql = 'INSERT INTO hpo VALUES (?,?,?,?)'
        db_c.executemany(sql,values)
        self.db_conn.commit()
    @property
    def name(self):
        if getattr(self,'_name',None) is None:
            db_c = self.db_conn.cursor()
            db_c.execute('SELECT * FROM hpo WHERE id=?',(self.id,))
            db_hpo = dict_factory(db_c,db_c.fetchone())
            if db_hpo == None or db_hpo['name'] == None:
                # first check if hpo db has been constructed
                _check_db()
                raise 'no name can be retrieved'
            else:
                name = db_hpo['name']
            self._name = name
        return self._name
    
    @property
    def parents(self):
        if getattr(self,'_parents',None) is None:
            db_c = self.db_conn.cursor()
            db_c.execute('SELECT * FROM hpo WHERE id=?',(self.id,))
            db_hpo = dict_factory(db_c,db_c.fetchone())
            if db_hpo == None or db_hpo['parents'] == None:
                # first check if hpo db has been constructed
                _check_db()
                raise ValueError('no parents can be retrieved')
            else:
                parents = json.loads(db_hpo['parents'])
            self._parents = parents
        return self._parents

    @property
    def ancestors(self):
        if getattr(self,'_ancestors',None) is None:
            db_c = self.db_conn.cursor()
            db_c.execute('SELECT * FROM hpo WHERE id=?',(self.id,))
            db_hpo = dict_factory(db_c,db_c.fetchone())
            if db_hpo == None or db_hpo['ancestors'] == None:
                # first check if hpo db has been constructed
                _check_db()
                raise ValueError('no ancestors can be retrieved')
            else:
                ancestors = json.loads(db_hpo['ancestors'])
            self._ancestors = ancestors
        return self._ancestors