'''
Programma regex kompilēšanai par automātu un pielietošanai uz teksta
Regex šajā gadījumā:
    | - kojukcija
    * - iterācija (0+)
    % - tukšums
    . - jebkura zīme
    (regex) - apakšizteiksme
    /operators , piem. /* - burtiski ņem operatoru kā alfabēta burtu
    (<grupas nosaukums>regex) , piem (<uzvards>regex) - notverošā grupa
'''

from dataclasses import replace
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
    
    def __init__(self, regex : str, checkForErrors = True):
        '''
        Izveido automātu no regex
        Ja checkForErrors = False, izlaiž sintakses pārbaudi, 
        bet tas var rezultēties nedefinētā rezultātā.

        skipStandartize - atstāt False   
        '''

        #kompilē NFA un pārvērš par DFA (pieņemot, ka neesošās ievades noved pie deadstate)
        #Pārveido stāvokļu nosaukumus par str, jo tas nepieciešams visual-automata bibliotēkai  
        self.regex = regex
        if checkForErrors:
            error = self.__checkForErrors(regex)
            if error != None:
                raise Exception(error)
        NFA, accepting1, _, _, capturingGroupsNFA = self.__compileNFA(regex) 
        ind = 1 #nākamā stāvokļa indekss
        DFA = {} #Automāta pārejas 
        q = Queue() #DFA stāvokļu nosaukumi 
        dictionary1 = {0 : (0,)} #DFA : (NFA konjukcijas)
        dictionary2 = {(0,) : 0} #(NFA konjukcijas) : DFA
        visited = {} #Jau izskatītie stāvokļi
        accepting2 = set() # Akceptējošie stāvokļi
        self.states = {'0'} #Vizualizācijai saglabā sarakstu ar stāvokļiem
        q.put(0)  #Sāk ar 0 DFA stāvokli
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

        self.capturingGorups = {} #{nosaukums : {start_1, start_2 ,..., start_n}, {accepting_1, accepting_2 ,..., accepting_n}])}

        #pārtuklko notverošas grupas
        if len(capturingGroupsNFA) > 0:
            dictionary3 = {} # {NFA stāvoklis : DFA stāvoklis}
            for DFAState, NFAStates in dictionary1.items():
                for state in NFAStates:
                    dictionary3[state] = DFAState 

        for cgname, (starts, ends) in capturingGroupsNFA.items():            
            startsDFA = set()
            endsDFA = set()
            for state in starts:
                startsDFA.add(str(dictionary3[state]))
            for state in ends:
                endsDFA.add(str(dictionary3[state]))    

            self.capturingGorups[cgname] = (startsDFA, endsDFA)

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
                if 'any' in inputs:
                    state = next(iter(inputs['any']))
                else:
                    return False
            else:
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
        input_symbols={c for c in self.regex}|{'any'},
        transitions=self.table,
        initial_state='0',
        final_states=self.accepting,
        )
        nfa = VisualNFA.eliminate_lambda(nfa)
        nfa.show_diagram(filename=visualName, path=visualPath)

    def find(self, text : str, start = 0, coverAllow = False):
        '''
            Atrod visas vietas text sākot ar start indeksu, kas akceptējas ar šo regex objektu
            Ja coverAllow = False, izlaiž pārklājošās virknes (prioritizējot garākās)
            Atgriež tās kā ģeneratoru: ((sākuma indekss, beigu indekss, atrastais teksts, {grupas nosaukums : notverošas grupas tādā pašā formātā kā kopējais}, ...) 
        '''
        i = start 
        capturedGroups = {}  #rezultātu dati atrastajām grupām
        while i<len(text):
            groupsStarts = {} #{grupas nosaukums : starta indekss}
            currFound = None #atrastā apakšvirkne, ko pievienos matches beigās (vajadzīgs coverAllow = False)
            state = '0'
            for pos, c in enumerate(text[i:]):
                for groupName, (starts, ends) in self.capturingGorups.items():
                    if state in starts and not groupName in groupsStarts:
                        groupsStarts[groupName] = i+pos
                if not state in self.table:
                    break
                inputs = self.table[state]
                if not c in inputs:
                    if 'any' in inputs:
                        state = next(iter(inputs['any']))
                    else:
                        break
                else:
                    state = next(iter(inputs[c])) #Tā kā tiek pilietots DFA pieņemam ka pirmais kopas elements ir vienīgais
                for groupName, start in groupsStarts.items():
                    if state in self.capturingGorups[groupName][1]:
                        capturedGroups[groupName] = (start, i+pos+1, text[start:i+pos+1])    
                if state in self.accepting:
                    if coverAllow:
                        fullCapturedGroups = dict(capturedGroups)
                        for groupName in self.capturingGorups.keys():
                            if groupName not in capturedGroups:
                                if groupName not in groupsStarts:
                                    groupsStarts[groupName] = pos+1
                                fullCapturedGroups[groupName] = (groupsStarts[groupName], groupsStarts[groupName], "") 
                        yield (i, i+pos, text[i:i+pos+1], fullCapturedGroups)
                    else:
                        currFound = (i, i+pos+1, text[i:i+pos+1], capturedGroups)
            if not coverAllow and currFound != None:
                for groupName in self.capturingGorups.keys():
                    if groupName not in capturedGroups:
                        if groupName not in groupsStarts:
                            groupsStarts[groupName] = pos+1
                        capturedGroups[groupName] = (groupsStarts[groupName], groupsStarts[groupName], "") 
                yield currFound
                i += pos+1
            else:
                i+=1                     

    def replace(self, text : str, replaceText, start = 0, groupFunctions = None):
        '''
            Atrod text nepārklājošas (prioritizējot garākās) virknes, kas atbilst šim regex,
            aizvieto tās ar replaceText
            Sāk meklēt ar start indeksu
            
            replaceText var saturēt {grupas nosaukums}, piemēram, "Labdien, {Vards}!", 
            ko aizvietos ar attiecīgo grupu regex, kuras nosaukums ir "Vards".

            groupFunctions formāts : {grupas nosaukums : funkcija(str)->str}, 
            grupa pirms aizvietošanas tiks apstrādāta funckijā, kura atgriež patieso aizvietošanas vērtību,
            ja grupas nosaukums eksistē iekš groupFunctions
        '''

        #sagatavo grupas aizvietošanai
        groupRegex = Regex('{(<groupName>..*)}', checkForErrors=False)
        groups = list(groupRegex.find(replaceText, coverAllow=False))
        for (_,_,_,groupNameDict) in groups:
            groupName = groupNameDict["groupName"][2]
            if groupName not in self.capturingGorups:
                raise Exception(f"Grupa {groupName} neeksistē.")
        #aizvietošana
        matches = self.find(text, start=0, coverAllow=False)
        prevEnd = -1 #iepriekšējās konkatenācijas beigas
        newText = "" #aizvietotais teksts
        for match in matches:
            #aizvieto grupas replaceText
            modifiedReplaceText = ""
            prevEndGroups = -1
            for (start, end, _, groupNameDict) in groups:
                groupName = groupNameDict["groupName"][2]
                replaceValue = match[3][groupName][2]
                if groupFunctions != None and groupName in groupFunctions:
                    replaceValue = groupFunctions[groupName](replaceValue)    
                modifiedReplaceText += replaceText[prevEndGroups+1:start] + replaceValue
                prevEndGroups = end-1
            modifiedReplaceText += replaceText[prevEndGroups+1:len(replaceText)]
            # print(f"text: {modifiedReplaceText}")
            #aizvieto ar replaceText
            newText += text[prevEnd+1:match[0]] + modifiedReplaceText
            prevEnd = match[1]-1
        return newText + text[prevEnd+1:len(text)]    

    def __checkForErrors(self, regex : str):
        '''
        Pārbauda vai regex sintakse ir pareiza:
        1) Visas iekavas ir aizvērtas
        2)| un * seko pēc alfabēta burta, % vai )
        3) Regex nav tukša virkne (bez atstarpēm)
        4) Iekavas nav tukšas
        5)| seko alfabēta burts, % vai (
        6) Grupu nosaukumi neatkārtojas un nesatur '<', ')', '(' 
        7)Grupu sākuma operators < ir balansēts un nav tukšs, atrodas tikai apakšizteiksmes sākumā
        8)/ seko kāda zīme  

        Ja kļūdu nav atgriež None, ja ir str, kas paskaidro pirmo atrasto kļūdu un tās indeksu
        '''

        if regex == "":
            return "Tukšs regex nav atļauts. Ja gribat akceptēt tukšumu, rakstiet '%'"

        stack = []
        
        lastalpha = False

        conjLast = False
        conjInd = -1

        lastOpenParenthesis = False

        literal = False

        groupNamesUsed = set()
        i = 0
        while i < len(regex):
            c = regex[i]
            if literal:
                if i+1 == len(regex):
                    return "/ operators nav atļauts beigās, lietojiet '//', lai burtiski prasītu '/'!"
                literal = False
                lastalpha = True
                lastOpenParenthesis = False
                conjLast = False 
            elif c == ' ':
                pass
            elif c == '<':
                if not lastOpenParenthesis:
                    return f"Pozīcijā {i} nav atļauts grupas nosaukums"    
                empty = True
                NO_MATCH_ERROR = f"Pozīcijā {i} '<' netiek aizvērts"
                i+=1
                if i==len(regex):
                    return NO_MATCH_ERROR
                groupName = ""    
                while regex[i] != '>':
                    if regex[i] == ' ':
                        i+=1
                        continue 
                    empty = False 
                    if i+1==len(regex) or regex[i] in {'<', '(', ')'}:
                        return f"Pozīcijā {i} neatļauta zīme grupas nosaukumā."
                    groupName += regex[i]
                    i+=1
                if empty:
                    return f"Tukšs grupas nosaukums pozīcijā {i}"
                if groupName in groupNamesUsed:
                    return f"Otreiz izmantots grupas nosaukums {groupName} pozīcijā {i-len(groupName)}"
                groupNamesUsed.add(groupName)    
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
            elif c == '/':
                literal = True
            else:
                lastalpha = True
                lastOpenParenthesis = False
                conjLast = False
            i+=1    
    
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

        Atgriež : automāta pārejas, akceptējošo stāvokli, nākamo indeksu, vai radītais automāts akceptē tukšumu, 
                    notverošās grupas ({nosaukums : {start_1, start_2 ,..., start_n}, {accepting_1, accepting_2 ,..., accepting_n}])})
        '''
        def mathchingParenthesesIndex(string, open):
            '''
            Atrod indeksu iekavai, kas aizver iekavu open indeksā string virkne 
            Ja nav atgriež -1
            '''
            openCount = 1
            prevLiteral = False
            for i in range(open+1, len(string)):
                if prevLiteral:
                    prevLiteral = False
                    continue
                if string[i] == '/':
                    prevLiteral = True
                    continue
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
        capturingGroups = {} # {nosaukums : {start_1, start_2 ,..., start_n}, {accepting_1, accepting_2 ,..., accepting_n}])}
        nextCaptureName = None # Sekojošās notverošās grupas nosaukums  
        while pos < len(regex):
            c = regex[pos]
            if c == '/':
                pos+=1
                c = regex[pos]
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
            elif c == "|":
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
                if regex[pos+1] == '<':
                    end = regex.find('>', pos+2)
                    nextCaptureName = regex[pos+2:end]
                    pos += len(nextCaptureName) + 2
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
                sub, suba, ind, conjoptional, subCaptuingGroups = self.__compileNFA(substr, sind = ind+1)

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

                #Notverošo grupu pievienošana
                for cgname, (starts, ends) in subCaptuingGroups:
                    starts
                    ends
                    if subStart in starts:
                        starts.remove(subStart)
                        for sa in accepting1:
                            starts.add(sa)        
                    if subStart in ends:
                        ends.remove(subStart)
                        for sa in accepting1:
                            ends.add(sa)
                    capturingGroups[cgname] = (starts, ends)                    

                if nextCaptureName != None:
                    ends = suba
                    if subStart in suba:
                        ends.remove(subStart)
                        for sa in accepting1:
                            ends.add(sa) 
                    capturingGroups[nextCaptureName] = (set(accepting1), ends) 
                    nextCaptureName = None
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
                if c == '.':
                    c = 'any'
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

        return NFA, accepting1, ind, optionalsub, capturingGroups        

    

def main():

    #Pielietojuma piemēri

    # regex = Regex('(A | (BA) | C)*')

    # print(regex.isAccepted(""))
    # print(regex.isAccepted("A"))
    # print(regex.isAccepted("B"))
    # print(regex.isAccepted("BA"))
    # print(regex.isAccepted("CBA"))
    # print(regex.isAccepted("CC"))
    # print(regex.isAccepted("D"))

    # regex= Regex('(AA(A|B)*AA)|(BB(A|B)*BB)|(AB(A|B)*AB)|(BA(A|B)*BA)|A|B|(AA)|(AAA)|(BBB)|(BB)')

    # print(regex.isAccepted("AA"))
    # print(regex.isAccepted("A"))
    # print(regex.isAccepted("B"))
    # print(regex.isAccepted("ABBBAB"))
    # print(regex.isAccepted("BBAAAA"))
    # print(regex.isAccepted("ABA"))
    # print(regex.isAccepted(""))
    # regex = Regex('(0|1)0*%|1')

    # print(regex.isAccepted("00001"))
    # print(regex.isAccepted("1000"))
    # print(regex.isAccepted("000"))
    # regex.saveVisualAutomata("C:\Temp")

    # regex = Regex('.8.*9')

    # print(regex.isAccepted("087729"))
    # print(regex.isAccepted("087721"))
    # print(regex.isAccepted("87729"))
    # regex.saveVisualAutomata("C:\Temp")

    # regex = Regex('(Tom) | (Julie) | (Nigel)')
    # print(regex.replace("The defendant Tom was acused by the plaintiff Julie, Nigel provided witness testimony.", "[Name redacted]"))

    # regex = Regex('A(<first>ABCD)(<second>H*)', checkForErrors=False)
    # # regex.saveVisualAutomata("C:\Temp")
    # # print(regex.capturingGorups)
    # print(list(regex.find("AABCD", coverAllow = False)))
    # regex = Regex('(<number>(1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*)', checkForErrors=False)
    # regex.saveVisualAutomata("C:/Temp")
    # print(regex.replace("8 234 918", "({number})", groupFunctions={"number" : lambda n : str(int(n)*12) }))
    pass


if __name__ == "__main__":
    main()








