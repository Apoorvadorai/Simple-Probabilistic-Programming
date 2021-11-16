from lark import Lark, Transformer, v_args
from lark import Token,Tree
import random
import copy
import time

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
    vals =[]
    if t.data =='p':
        traces = statement(t.children[0], vals)
        return result(t.children[1],traces)
    
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
    elif t.data =='observe':
         traces = observe(t.children[0],traces)
         
    return traces

def result(t,traces):
    prb =[]
    if (isinstance(t.children[0], Token)):
        z = sum([tr[1] for i, tr in enumerate(traces)])
        for i, tr in enumerate(traces):
            if (str(t.children[0]),True) in tr[0].items():

                prb.append(tr[1])
        return (sum(prb)/z)
    else:
        traces = expression(t.children[0],traces)
        prb =[tr[1] for i,tr in enumerate(traces)]
        return (sum(prb))


def flip(t,traces):
    if len(traces)==0:
        traces.append([{str(t[0]):True},float(t[1])])
        traces.append([{str(t[0]):False},1-float(t[1])])
    else:
        new_trace = copy.deepcopy(traces)
        for i in range(len(traces)):
            traces[i][0].update({str(t[0]):True})
            traces[i][1]= traces[i][1]*float(t[1])
            
        for i in range(len(new_trace)):
            new_trace[i][0].update({str(t[0]):False})
            new_trace[i][1]= new_trace[i][1]*(1-float(t[1]))
        traces = traces + new_trace
    return traces


def if_clause(tree,traces):
    guard = expression(tree[0],traces)
    if isinstance(guard,str):
        guard = [tr for tr in traces if (guard,True) in tr[0].items()]
    non_guard = [ tr for tr in traces if tr not in guard]
    left = statement(tree[1],guard)
    right = statement(tree[2],non_guard)
    traces = left +right
    return traces

def expression(tree, traces):
    if tree.data =='or':
        left = expression(tree.children[0],traces)
        right = expression(tree.children[1],traces)
    
        if isinstance(right, str):
            new_traces = [tr for tr in traces if ((left,True) in tr[0].items()) or\
                          ((right,True)in tr[0].items())]
            return new_traces
        else:
            return right
        
    elif tree.data =='e':
        if isinstance(tree.children[0],Token):
            return (str(tree.children[0]))
        else: 
            return(expression(tree.children[0],traces))
    elif tree.data =='and':
        left = expression(tree.children[0],traces)
        right = expression(tree.children[1],traces)

        if (isinstance(right, str)):
            new_traces = [tr for tr in traces if ((right,True)in tr[0].items()) \
                          and ((left,True)in tr[0].items()) ]
            return new_traces
        else:
            
            traces = [tr for tr in right if ((left,True) in tr[0].items())]
            return traces
    elif tree.data  =='not':
        left = expression(tree.children[0],traces)
        traces = [tr for tr in traces if ((left,False) in tr[0].items())]
        return traces

def observe(t,traces):
    new_traces = expression(t,traces)
    if isinstance(new_traces,str):
        new_traces = [tr for tr in traces if (new_traces,True) in tr[0].items()]
    return new_traces

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
print("Time Taken : {}".format((end_time - start_time)/1000000))
print("--"*10)

        
parse_tree = simppl_parser.parse(noisy_or)
start_time = time.time_ns()
print("noisy_or : {}".format(inference(parse_tree)))
end_time = time.time_ns()
print("Time Taken : {}".format((end_time - start_time)/1000000))
print("--"*10)
    
parse_tree = simppl_parser.parse(chain)
start_time = time.time_ns()
print("chain : {}".format(inference(parse_tree)))
end_time = time.time_ns()
print("Time Taken : {}".format((end_time - start_time)/1000000))
print("--"*10)

parse_tree = simppl_parser.parse(burglar_alarm)
start_time = time.time_ns()
print("burglar_alarm : {}".format(inference(parse_tree)))
end_time = time.time_ns()
print("Time Taken : {}".format((end_time - start_time)/1000000))
