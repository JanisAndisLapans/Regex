'''
Programma regex kompilēšanai par automātu un pielietošanai uz teksta
Regex šajā gadījumā:
| - kojukcija
* - iterācija (0+)
% - tukšums
(regex) - apakšizteiksme
'''

from importlib.resources import path
from queue import Queue
from turtle import st
from automata.fa.nfa import NFA
from visual_automata.fa.nfa import VisualNFA

#Šis ir vajadzīgs, ja grib lietot grafisko attēlojumu
#Instalējiet Graphviz uz GRAPHVIZ_PATH 
GRAPHVIZ_PATH = 'C:/Program Files'
import os
os.environ["PATH"] += os.pathsep + GRAPHVIZ_PATH + '/Graphviz/bin'

class Regex:
    
    def __init__(self, regex : str):
        '''
        Izveido automātu no regex
        '''

        #kompilē NFA un pārvērš par DFA (pieņemot, ka neesošās ievades noved pie deadstate)
        #Pārveido stāvokļu nosaukumus par str, jo tas nepieciešams visual-automata bibliotēkai  
        self.regex = regex
        error = self.__checkForErrors(regex)
        if error != None:
            raise Exception(error)
        NFA, accepting1, _, _ = self.__compileNFA(regex) 
        ind = 1 #nākamā stāvokļa indekss
        DFA = {} #Automāta pārejas 
        q = Queue() #DFA stāvokļu nosaukumi 
        q.put(0)  #Sāk ar 0
        dictionary1 = {0 : (0,)} #DFA : (NFA conjuncts)
        dictionary2 = {(0,) : 0} #(NFA conjuncts) : DFA
        visited = {} #Jau izskatītie stāvokļi
        accepting2 = set() # Akceptējošie stāvokļi
        self.states = {'0'} #Vizualizācijai saglabā sarakstu ar stāvokļiem 
        while not q.empty():
            state = q.get()
            if state in visited:
                continue
            conjs = dictionary1[state]
            idests = {}
            for c in conjs:
                cstate = NFA[c] if c in NFA else {}
                for input, dests in cstate.items():
                    for dest in dests:
                        if not input in idests:
                            idests[input] = set()
                        idests[input].add(dest)
                if c in accepting1:
                    accepting2.add(str(state))    
            for input, dests in idests.items():
                tdests = tuple(dests)
                if tdests in dictionary2:
                    name = dictionary2[tdests]
                else:
                    name = ind
                    self.states.add(str(ind))
                    ind+=1
                    dictionary1[name] = tdests
                    dictionary2[tdests] = name
                self.__addToAutomata(DFA, str(state), input, str(name))
                q.put(name)
            visited[state] = True     

        for state in self.states:
            if not state in DFA:
                    DFA[state] = {} 

        self.accepting = accepting2
        self.table = DFA
    
    def isAccepted(self, text : str):
        '''
        Nosaka vai regex akceptēs text
        Start ir sākuma stāvoklis automātam
        Atgriež True vai False
        '''
        state = '0'
        for c in text:
            if not state in self.table:
                return False
            inputs = self.table[state]
            if not c in inputs:
                return False
            state = next(iter(inputs[c])) #Tā kā tiek pilietots DFA pieņemam ka pirmais kopas elements ir vienīgais
        return state in self.accepting

    def saveVisualAutomata(self, visualPath : str, visualName = "visual"):
        '''
        Izveido grafisku attēlojumu automātam un saglabā png
        visualPath/visualName.png

        Izmanto visual-automata bibliotēku
        '''      
        nfa = VisualNFA(
        states=self.states,
        input_symbols={c for c in self.regex if not c in ['(', ' ', ')', '*', '%', '|']},
        transitions=self.table,
        initial_state='0',
        final_states=self.accepting,
        )
        nfa = VisualNFA.eliminate_lambda(nfa)
        nfa.show_diagram(filename=visualName, path=visualPath)

    def __checkForErrors(self, regex : str):
        '''
        Pārbauda vai regex sintakse ir pareiza:
        1) Visas iekavas ir aizvērtas
        2)| un * seko pēc alfabēta burta, % vai )
        3) Regex nav tukša virkne (bez atstarpēm)
        4) Iekavas nav tukšas
        5)| seko alfabēta burts, % vai ( 

        Ja kļūdu nav atgriež None, ja ir str, kas paskaidro pirmo atrasto kļūdu un tās indeksu
        '''

        if regex == "":
            return "Tukšs regex nav atļauts. Ja gribat akceptēt tukšumu, rakstiet '%'"

        stack = []
        
        lastalpha = False

        conjLast = False
        conjInd = -1

        lastOpenParenthesis = False

        for i, c in enumerate(regex):
            if c == ' ':
                continue
            elif c == '(':
                lastOpenParenthesis = True
                lastalpha = False 
                stack.append(i)
                conjLast = False
            elif c == ')':
                if lastOpenParenthesis:
                    return f"Tukšas iekavas {i} pozīcijā"
                lastalpha == True
                if len(stack) == 0:
                    return f"Iekava ) {i} pozīcijā neko neaizver"
                stack.pop()
                lastOpenParenthesis = False
            elif c == '|':
                conjLast = True
                conjInd = i
                if not lastalpha:
                    return f"| pozīcijā {i} ir neatļauts"
                lastalpha = False 
                lastOpenParenthesis = False
            elif c == '*':
                if not lastalpha:
                    return f"* pozīcijā {i} ir neatļauts"
                lastalpha = False 
                lastOpenParenthesis = False
            else:
                lastalpha = True
                lastOpenParenthesis = False
                conjLast = False
    
        if len(stack) > 0:
            return f"Iekava {stack[0]} pozīcijā nav aizvērta"           
        elif conjLast:
            return f"Nepabeigta konjukcija {conjInd} pozīcijā"
        return None        



    def __addToAutomata(self, automata, name, input, to):
            '''
            Funkcija, lai pievienotu automātam automata,
            ceļu no name uz to ar input ievadi

            automata attēlo:
            {name: {input : {to1, to2, ..., ton}, ...}, ...}
            '''
            if not name in automata:
                automata[name] = {}
            if not input in automata[name]:
                automata[name][input] = set()
            automata[name][input].add(to)
    def __compileNFA(self, regex : str, sind = None):
        '''
        Izveido nedeterminētu automātu no regex jeb tādu, 
        kuram var būt vairāki ceļi no vienas ievades
        Nepieciešams, lai izveidotu pilno automātu

        sind ir nākamais indekss jaunam stāvoklim

        Atgriež : automāta pārejas, akceptējošo stāvokli, nākamo indeksu, vai radītais automāts akceptē tukšumu
        '''
        def mathchingParenthesesIndex(string, open):
            '''
            Atrod indeksu iekavai, kas aizver iekavu open indeksā string virkne 
            Ja nav atgriež -1
            '''
            openCount = 1
            for i in range(open+1, len(string)):
                if string[i] == "(":
                    openCount+=1
                elif string[i] == ")":    
                    openCount-=1
                    if openCount==0:
                        return i
            return -1            
            
        regex = regex.replace(" ", "") # Neņem vērā atstarpes jeb 'A | B' = 'A|B'
        if sind == None:
            ind = 1
        else:
            ind = sind        
        NFA = {} #Automāta pārejas
        accepting1 = set() # Akceptējošie stāvokļi
        conjnext = False #Nākamā alfabēt zīme vai apakšizteiksme ir konjukcija ar iepriekšējo
        optionalsub = True #Vai automāts akceptē tukšumu?
        firstconj = True #Vai jau ir sasniegta vismaz viens alfabēta simbols? 
                        #Vajadzīgs, lai optionalsub pareizi strādātu ar regex, kas nesatur alfabēta simbolus      
        conjoptional = False # šobrīdējā konjukcija (tai skaitā viena ievade, kas ir konjukcijā tikai ar sevi)
                            # akceptē tukšumu  
        nextLayer = {ind-1} # Nākamā slāņa jeb konkatenācijas stāvokļi
        pos = 0 #Pozīcija virknē regex 
        while pos < len(regex):
            c = regex[pos]
            if c == "|":
                conjnext = True
            elif c == "*":
                for le in lastend:
                    for i, ch in last:
                        self.__addToAutomata(NFA, le, ch, i)
                conjoptional = True
            elif c == "%":
                if not conjnext:
                    if conjoptional:
                        conjoptional = False
                        accepting1 |= nextLayer
                        nextLayer = set()
                    else:
                        accepting1 = nextLayer
                        nextLayer = set()
                conjoptional = True
            elif c == "(":
                if not conjnext:
                    if conjoptional:
                        conjoptional = False
                        accepting1 |= nextLayer
                        nextLayer = set()
                    else:
                        optionalsub = False if not firstconj else optionalsub
                        accepting1 = nextLayer
                        nextLayer = set()
                firstconj = False
                skip = mathchingParenthesesIndex(regex, pos)
                subStart = ind
                substr = regex[pos+1:skip]
                sub, suba, ind, conjoptional = self.__compileNFA(substr, sind = ind+1)
                nextLayer |= suba
                for si, s in sub.items():
                    if si == subStart:
                        continue
                    for input, dests in s.items():
                        for dest in dests:
                            if dest == subStart:
                                for a in accepting1:
                                    self.__addToAutomata(NFA, si, input, a)
                            else:
                                self.__addToAutomata(NFA, si, input, dest)                      
                for s in accepting1:
                    for input, dests in sub[subStart].items():
                        for dest in dests:
                            if dest == subStart:
                                for a in accepting1:
                                    self.__addToAutomata(NFA, s, input, a)
                            else:
                                self.__addToAutomata(NFA, s, input, dest)

                last  = []
                for a in accepting1:
                    for ch, dests in NFA[a].items():
                        for dest in dests:
                            last.append((dest, ch))
                lastend = list(suba)
                conjnext = False
                pos = skip
            else:
                if not conjnext:
                    if conjoptional:
                        conjoptional = False
                        accepting1 |= nextLayer
                        nextLayer = set()
                    else:
                        optionalsub = False if not firstconj else optionalsub
                        accepting1 = nextLayer
                        nextLayer = set()
                firstconj = False        
                nextLayer.add(ind)             
                for s in accepting1:
                    self.__addToAutomata(NFA, s, c, ind)
                last  = [(ind, c)] 
                lastend = [ind]
                ind+=1
                conjnext = False
            pos+=1

        if conjoptional:
            accepting1 |= nextLayer
        else:
            optionalsub = False if not firstconj else optionalsub
            accepting1 = nextLayer   
        return NFA, accepting1, ind, optionalsub        

    

def main():

    #Pielietojuma piemēri

    regex = Regex('(A | (BA) | C)*')

    print(regex.isAccepted(""))
    print(regex.isAccepted("A"))
    print(regex.isAccepted("B"))
    print(regex.isAccepted("BA"))
    print(regex.isAccepted("CBA"))
    print(regex.isAccepted("CC"))
    print(regex.isAccepted("D"))

    regex= Regex('(AA(A|B)*AA)|(BB(A|B)*BB)|(AB(A|B)*AB)|(BA(A|B)*BA)|A|B|(AA)|(AAA)|(BBB)|(BB)')

    print(regex.isAccepted("AA"))
    print(regex.isAccepted("A"))
    print(regex.isAccepted("B"))
    print(regex.isAccepted("ABBBAB"))
    print(regex.isAccepted("BBAAAA"))
    print(regex.isAccepted("ABA"))
    print(regex.isAccepted(""))
    regex = Regex('(0|1)0*%|1')

    print(regex.isAccepted("00001"))
    print(regex.isAccepted("1000"))
    print(regex.isAccepted("000"))
    regex.saveVisualAutomata("C:\Temp")

if __name__ == "__main__":
    main()








