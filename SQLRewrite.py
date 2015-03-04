import sqlparse
import re
from django.conf import settings

bad_chars= '\'`"'

def normalize(name):
	if len(name) > 0:
		return ''.join(c for c in name if c not in bad_chars)
	return None

#Returns: configuration parameter or None
def in_secure_tables(table):
	for p in settings.SQL_REWRITE_REGEXP:
		if p[0].split('.')[0]==table:
			return p
	return None

#Returns: pointers to WHERE and JOIN (INNER, LEFT, RIGHT) statements
def is_where_and_ij(tk):
	ij_flag = None
	w_flag = None
	for x in xrange(len(tk)):
		if tk[x].match(sqlparse.tokens.Token.Keyword,'.*JOIN.*',regex=True)==True:
			ij_flag = x
		if tk[x].match(None,'WHERE') == True:
			w_flag = x
	return w_flag,ij_flag

#Returns: From pointer (fp) and table alias (tmp_s[-1])
def from_alias(tk,name):
		c=0
		while tk[c].value!='FROM':
			c+=1
		fp=c
		c+=2
		ms = '.*'+name+'.*'
		tbs = tk[c].value.split(',')
		for x in tbs:
			if re.match(ms,x) is not None:
				tmp_s = x.split(' ')
				return fp,tmp_s[-1]
		return fp,None

def rewrite_query(sql,params,uname):

	msql=sqlparse.format(sql, reindent=False, keyword_case='upper')
	mparams=params
	
	pst=sqlparse.parse(sql)
	st=pst[0].tokens
	if st[0].match(sqlparse.tokens.Keyword.DML,'SELECT')==True:
		for x in xrange(len(st)):
			if st[x].match(sqlparse.tokens.Token.Keyword,'FROM'):
				table = normalize(st[x+2].value)
				param=in_secure_tables(table)
				if param is not None: 
					msql=rewrite_sel_query(pst,uname,param)
				
	return msql,mparams


def rewrite_sel_query(pst,uname,param):
	mess = param[1] 
	tb, column_name = param[0].split('.')
	if '%s' in mess:
		mess = mess % uname
	c=0
	tk = pst[0].tokens
	num_tk = len(tk)
	wh, ij = is_where_and_ij(tk)
	fp,na = from_alias(tk,tb)
	if wh is not None and ij is None:
		pst[0].tokens.insert(wh+2,sqlparse.sql.Token(None,"`"+tb+"`.`"+column_name+"` REGEXP '"+mess+"' AND "))
	elif wh is None and ij is None:
		fp+=4
		if fp>=num_tk:
			pst[0].tokens.append(sqlparse.sql.Token(None," `"+tb+"`.`"+column_name+"` REGEXP '"+mess+"'"))
		else:
			pst[0].tokens.insert(fp,sqlparse.sql.Token(None,"WHERE `"+tb+"`.`"+column_name+"` REGEXP '"+mess+"' "))
	
	elif wh is not None and ij is not None:
		tmp=na
		if na is None:
			tmp = column_name
		pst[0].tokens.insert(wh+2,sqlparse.sql.Token(None,"`"+tmp+"`.`"+column_name+"` REGEXP '"+mess+"' AND "))
	elif wh is None and ij is not None:
		c=fp
		while tk[c].match(sqlparse.tokens.Token.Keyword,'ON')!=True:
			c+=1
		tmp=na
		if na is None:
			tmp = column_name
		pst[0].tokens.insert(c+2,sqlparse.sql.Token(None,"`"+tmp+"`.`"+column_name+"` REGEXP '"+mess+"' AND "))
			
	return unicode(pst[0])