from lark import Lark, Transformer, v_args
from lark import Token,Tree
import random
import copy
import time
import numpy as np

simppl_grammer= r"""
e: NAME
  | and
  | or
  | not
  | "true" -> true
  | "false" -> false

and: "(" "&&" e e ")"
or: "(" "||" e e ")"
not: "(" "!" e ")"

s: assgn
  | flip
  | observe
  | ite
  | seq

assgn: NAME "=" e
flip: NAME "~" "flip" SIGNED_NUMBER
observe: "observe" e
seq: s ";" s
ite: "if" e "{" s "}" "else" "{" s "}"

p: s ";" "return" e
  %import common.SIGNED_NUMBER
  %import common.WS
  %import common.CNAME -> NAME
  %ignore WS
"""
simppl_parser = Lark(simppl_grammer, start="p")

def inference(t):
    sampling =[]
    for i in range(50000):
        if t.data =='p':
            vals =[]
            traces = (statement(t.children[0], vals))
            if len(traces) != 0 :
                sampling.append(result(t.children[1],traces))
    rejected = [1 for i in range(len(sampling)) if sampling[i]== True]
    return(sum(rejected)/len(sampling))


def statement(t, traces):
    if t.data =='s':
        traces = (statement(t.children[0],traces))
    elif t.data == 'seq':
        childs = t.children
        for child in childs:
            traces = (statement(child,traces))
    elif t.data =='flip':
         traces = flip(t.children,traces)
    elif t.data =='e':
         traces = expression(t.children[0],traces)
    elif t.data == 'ite':
         traces = if_clause(t.children,traces) 
    elif t.data == 'observe':
         new_trace = expression(t.children[0],traces)
         if isinstance(new_trace,str):
             traces = [tr for i, tr in enumerate(traces) if (new_trace,True) in tr[0].items()]
         else: traces = new_trace
    return traces


def result(t,traces):
    if (isinstance(t.children[0], Token)):
        for i, tr in enumerate(traces):
            if (str(t.children[0]),True) in tr[0].items():
                return True
            else: return False
    else:
        traces = expression(t.children[0],traces)
        if len(traces)!=0:
            return True
        else : return False
        

def flip(t,traces):
    if len(traces)==0:
        if np.random.binomial(1, p= float(t[1]))==1:
            traces.append([{str(t[0]):True}])
        else:
            traces.append([{str(t[0]):False}])
    else:
        if np.random.binomial(1, p= float(t[1]))==1:
            for i in range(len(traces)):
                traces[i][0].update({str(t[0]):True})
        else: 
            for i in range(len(traces)):
                traces[i][0].update({str(t[0]):False})
    return traces


def if_clause(tree,traces):
    guard = expression(tree[0],traces)
    if isinstance(guard,str):
        for i, tr in enumerate(traces):
            if ((guard,True) in tr[0].items()):
                traces = statement(tree[1],traces) 
                return traces
            else:
                traces = statement(tree[2],traces)
                return traces
    elif len(guard)>0:
        traces = statement(tree[1],traces)
        return traces
    else: 
        
        traces = statement(tree[2],traces)
        return traces



def expression(tree, traces):
   if tree.data =='e':
        if isinstance(tree.children[0],Token):
            return (str(tree.children[0]))
        else: 
            return(expression(tree.children[0],traces))
   
   elif tree.data =='and':
        left = expression(tree.children[0],traces)
        right = expression(tree.children[1],traces)
        if isinstance(right,str):
            traces = [tr for i,tr in enumerate(traces) if ((left,True)in tr[0].items()) and ((right,True)in tr[0].items())]
        else:
            traces =[tr for i,tr in enumerate(right) if ((left,True)in tr[0].items())]
        return traces
   
   elif tree.data =='or':
        left = expression(tree.children[0],traces)
        right = expression(tree.children[1],traces)
        if isinstance(right, str) and isinstance(left,str):    
                traces = [tr for i,tr in enumerate(traces) if ((left,True)in tr[0].items()) or ((right,True)in tr[0].items())]
        else:
            return right
        return traces
   elif tree.data  =='not':
        left = expression(tree.children[0],traces)
        traces = [tr for tr in traces if ((left,False) in tr[0].items())]
        return traces



###############################Benchmarks##########

            
simple_conjunction = " x ~ flip 0.1 ; \
                      y ~ flip 0.2; \
                     return (&& x y)"

noisy_or = " a ~ flip 0.1 ; \
             b ~ flip 0.2 ; \
             c ~ flip 0.3 ;\
             d ~flip 0.4 ; \
             e ~flip 0.5 ; \
             observe ( || a (|| b (|| c (|| d e)))) ;\
             return a"

chain = " a ~ flip 0.1 ;\
          if a { b ~ flip 0.2} else { b ~ flip 0.4}; \
          if b { c ~ flip 0.2} else { c ~ flip 0.4};\
          if c { d ~ flip 0.2} else {d ~ flip 0.4};\
          if d {e ~ flip 0.2} else {e ~ flip 0.4};\
          observe e;\
         return a"
          
burglar_alarm = "burglar ~ flip 0.001;\
                 earthquake ~ flip 0.002; \
                  if (&& burglar  earthquake) {alarm ~ flip 0.95\
                 }  \
                 else {if (&& burglar (! earthquake)){\
                    alarm ~ flip 0.94 \
                    } else {if (&& earthquake (!burglar)){\
                    alarm  ~ flip 0.29} else {alarm ~ flip 0.001}}};\
                 if alarm {\
                    johncalls ~ flip 0.90 \
                }else {\
                    johncalls ~ flip 0.05 \
                }; \
                if alarm {\
                   marycalls ~ flip 0.7\
                   } else {\
                     marycalls ~ flip 0.01 \
                };\
                observe (|| johncalls marycalls);\
                return earthquake"       
      
         
parse_tree = simppl_parser.parse(simple_conjunction)
start_time = time.time_ns()
print("simple_conjunction : {}".format(inference(parse_tree)))
end_time = time.time_ns()
print("Time Taken : {}".format((end_time - start_time)/10000000))
print("--"*10)

        
parse_tree = simppl_parser.parse(noisy_or)
start_time = time.time_ns()
print("noisy_or : {}".format(inference(parse_tree)))
end_time = time.time_ns()
print("Time Taken : {}".format((end_time - start_time)/10000000))
print("--"*10)
    
parse_tree = simppl_parser.parse(chain)
start_time = time.time_ns()
print("chain : {}".format(inference(parse_tree)))
end_time = time.time_ns()
print("Time Taken : {}".format((end_time - start_time)/10000000))
print("--"*10)

parse_tree = simppl_parser.parse(burglar_alarm)
start_time = time.time_ns()
print("burglar_alarm : {}".format(inference(parse_tree)))
end_time = time.time_ns()
print("Time Taken : {}".format((end_time - start_time)/10000000))
