'''
Programma regex kompilēšanai par automātu un pielietošanai uz teksta
Regex šajā gadījumā:
    | - kojukcija
    * - iterācija (0+)
    % - tukšums
    . - jebkura zīme
    (regex) - apakšizteiksme un nenosaukta notverošā grupa
    /operators , piem. /* - burtiski ņem operatoru kā alfabēta burtu
    (<grupas nosaukums>regex) , piem (<uzvards>regex) - notverošā grupa ar nosaukumu
    (?: regex izteiksme) - netverošā grupa jeb izteiksmi, kas sākas ar ?: neikļauj atrastajās grupās
    regex sākums(?<= regex izteiksme) - pozitīvā atpakaļskatīšana jeb izteiksmi, kas sākas ar ?<= neiekļauj meklēšanas rezultātos, un tā "neapēd" zīmes tekstā 
    regex sākums(?<! regex izteiksme) - negatīvā atpakaļskatīšana (tiek akceptēta negatīvi) jeb izteiksmi, kas sākas ar ?<! neiekļauj meklēšanas rezultātos, un tā "neapēd" zīmes tekstā 
    (?= regex izteiksme)regex beigas - pozitīvā priekšskatīšana jeb izteiksmi, kas sākas ar ?= neiekļauj meklēšanas rezultātos, un tā "neapēd" zīmes tekstā 
    (?! regex izteiksme)regex beigas - negatīvā priekšskatīšana (tiek akceptēta negatīvi) jeb izteiksmi, kas sākas ar ?! neiekļauj meklēšanas rezultātos, un tā "neapēd" zīmes tekstā 
    \s - atstarpe burtiski
    $ - rindas beigas
'''


from queue import Queue
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

        #kompilē NFA un pārvērš par DFA (pieņemot, ka neesošās ievades noved pie deadstate un tātad netiek iekļautas)
        #Pārveido stāvokļu nosaukumus par str, jo tas nepieciešams visual-automata bibliotēkai  
        self.regex = regex
        if checkForErrors:
            error = self.__checkForErrors(regex)
            if error != None:
                raise Exception(error)
        self.lookbehind = None
        self.lookahead = None

        if len(regex) > 4:
            if regex[0:3] == "(?<":
                if regex[3] == '=':
                    self.lookbehindPosititivity = True
                elif regex[3] == '!':
                    self.lookbehindPosititivity = False         
                end = self.__mathchingParenthesesIndex(regex, 0)
                self.lookbehind = Regex(regex[4:end], checkForErrors=False)
                regex = regex[end+1:]
        if regex[-1] == ')':
            openIndex = self.__mathchingParenthesesIndex2(regex, len(regex)-1)
            if openIndex != -1: #burtisks ')'
                group = regex[openIndex:]
                if len(group)>3:
                    if group[0:2] == '(?':
                        if group[2] == '=':
                            self.lookaheadPosititivity = True
                        elif group[2] == '!':
                            self.lookaheadPosititivity = False
                        self.lookahead = Regex(group[3:-1], checkForErrors=False)
                        regex = regex[:openIndex]        
        NFA, accepting1, _, _, capturingGroupsNFA, _ = self.__compileNFA(regex) 
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

        self.capturingGroups = {} #{nosaukums : {start_1, start_2 ,..., start_n}, {accepting_1, accepting_2 ,..., accepting_n}])}
        self.nonCapturingStates = set()

        #pārtuklko notverošas grupas un netverošās grupas
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

            self.capturingGroups[cgname] = (startsDFA, endsDFA)


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

        humanReadableTable = {}
        for state, inputs in self.table.items():
            stateInputs = {}
            humanReadableTable[state] = stateInputs
            for input, dest in inputs.items():
                if input == '\n':
                    input = 'new line'
                elif input == ' ':
                    input = 'space'
                stateInputs[input] = dest
 


        nfa = VisualNFA(
        states=self.states,
        input_symbols={c for c in self.regex}|{'any', 'space', 'new line'},
        transitions=humanReadableTable,
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

        lookBehindOks = set() #visas pozīcijas, kur beidzas self.lookbehind akceptēta apakšvirkne
        lookAheadOks = set() #visas pozīcijas, kur sākas self.lookahead akceptēta apakšvirkne

        if self.lookbehind != None:
            if self.lookbehind.isAccepted(""):
                lookBehindOks = {j-1 for j in range(len(text)+1)}
            else:        
            
                i = 0
                while i < len(text):
                    state = '0'
                    for j, c in enumerate(text[i:]):

                        if not state in self.lookbehind.table:
                            break
                        inputs = self.lookbehind.table[state]
                        if not c in inputs:
                            if 'any' in inputs:
                                state = next(iter(inputs['any']))
                            else:
                                break
                        else:
                            state = next(iter(inputs[c])) #Tā kā tiek pilietots DFA pieņemam ka pirmais kopas elements ir vienīgais            
                        
                        if state in self.lookbehind.accepting:
                            lookBehindOks.add(j+i)
        
                    i+=1        

        if self.lookahead != None:
            i = start+1
            if self.lookahead.isAccepted(""):
                lookAheadOks = {j for j in range(start+1, len(text)+1)}
            else:    
                while i < len(text):
                    state = '0'
                    for j, c in enumerate(text[i:]):

                        if not state in self.lookahead.table:
                            break
                        inputs = self.lookahead.table[state]
                        if not c in inputs:
                            if 'any' in inputs:
                                state = next(iter(inputs['any']))
                            else:
                                break
                        else:
                            state = next(iter(inputs[c])) #Tā kā tiek pilietots DFA pieņemam ka pirmais kopas elements ir vienīgais            
                        
                        if state in self.lookahead.accepting:
                            lookAheadOks.add(j+i)
                    i+=1          

        i = start 

        while i<len(text):
            if self.lookbehind != None:
                 if (i-1 in lookBehindOks) != self.lookbehindPosititivity:
                     i+=1
                     continue               

            capturedGroups = {}  #rezultātu dati atrastajām grupām
            groupStarts = {} #{grupas nosaukums : starta indekss}
            currFound = None #atrastā apakšvirkne, ko pievienos matches beigās (vajadzīgs coverAllow = False)
            state = '0'

            for pos, c in enumerate(text[i:]):
                for groupName, (starts, ends) in self.capturingGroups.items():
                    if state in starts and groupName not in groupStarts:
                        groupStarts[groupName] = i+pos

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

                for groupName, start in list(groupStarts.items()):
                    if state in self.capturingGroups[groupName][1]:
                        capturedGroups[groupName] = (groupStarts[groupName], i+pos+1, text[groupStarts[groupName]:i+pos+1])
                
                if self.lookahead != None and (i+pos+1 in lookAheadOks) != self.lookaheadPosititivity:
                    continue

                if state in self.accepting:
                    if coverAllow:
                        fullCapturedGroups = dict(capturedGroups)
                        for groupName in self.capturingGroups.keys():
                            if groupName not in capturedGroups:
                                if groupName not in groupStarts:
                                    groupStarts[groupName] = i+pos
                                fullCapturedGroups[groupName] = (groupStarts[groupName], groupStarts[groupName], "") 
                        yield (i, i+pos+1, text[i:i+pos+1], fullCapturedGroups)
                    else:
                        currFound = (i, i+pos+1, text[i:i+pos+1], capturedGroups)        

            if not coverAllow and currFound != None:
                
                for groupName in self.capturingGroups.keys():
                    if groupName not in capturedGroups:
                            if groupName not in groupStarts:
                                groupStarts[groupName] = i+pos
                            capturedGroups[groupName] = (groupStarts[groupName], groupStarts[groupName], "") 
                yield currFound
                i += (currFound[1] - currFound[0])
            else:
                i+=1
    

    def replace(self, text : str, replaceText, start = 0, groupFunctions = None):
        '''
            Atrod text nepārklājošas (prioritizējot garākās) virknes, kas atbilst šim regex,
            aizvieto tās ar replaceText
            Sāk meklēt ar start indeksu
            
            replaceText var saturēt {grupas nosaukums}, piemēram, "Labdien, {Vards}!", 
            ko aizvietos ar attiecīgo grupu regex, kuras nosaukums ir "Vards".
            Grupas ar {} tiks uzskatītas pēc kārtas par {'0'}, {'1'} ... {'n'}

            groupFunctions formāts : {grupas nosaukums : funkcija(str)->str}, 
            grupa pirms aizvietošanas tiks apstrādāta funckijā, kura atgriež patieso aizvietošanas vērtību,
            ja grupas nosaukums eksistē iekš groupFunctions
        '''

        #sagatavo grupas aizvietošanai
        groupId = 0
        groupRegex = Regex('{(<groupName>.*)}', checkForErrors=False)
        groups = list(groupRegex.find(replaceText, coverAllow=False))
        for (_,_,_,groupNameDict) in groups:
            groupName = groupNameDict["groupName"][2]
            if groupName == '':
                groupName = str(groupId)
                groupId+=1
            elif groupName.isnumeric():
                groupId = int(groupName)+1

            if groupName not in self.capturingGroups:
                raise Exception(f"Grupa {groupName} neeksistē, pozīcijā {groupNameDict['groupName'][0]}.")
        
        #aizvietošana
        matches = self.find(text, start=0, coverAllow=False)
        prevEnd = -1 #iepriekšējās konkatenācijas beigas
        newText = "" #aizvietotais teksts
        for match in matches:
            #aizvieto grupas replaceText
            modifiedReplaceText = ""
            prevEndGroups = -1
            groupId = 0
            for (start, end, _, groupNameDict) in groups:
                groupName = groupNameDict["groupName"][2]
                if groupName == '':
                    groupName = str(groupId)
                    groupId+=1
                elif groupName.isnumeric():
                    groupId = int(groupName)+1

                replaceValue = match[3][groupName][2]
                if groupFunctions != None and groupName in groupFunctions:
                    replaceValue = groupFunctions[groupName](replaceValue)    
                modifiedReplaceText += replaceText[prevEndGroups+1:start] + replaceValue
                prevEndGroups = end-1
            modifiedReplaceText += replaceText[prevEndGroups+1:len(replaceText)]
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
        9)?:, ?=, ?<=, ?!, ?<! tikai grupas sākumā
        10)Atpakaļskatīšanās tikai sākumā, priekšskatīšanās tikai beigās 


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

        groupModLast = False


        lastGroupReq = False
        isFirstGroup = True
        groupNamesUsed = set()
        i = 0
        while i < len(regex):
            c = regex[i]

            if lastGroupReq and len(stack) == 0:
                return "Priekšskatīšanai nedrīkst sekot zīmes!"

            if literal:
                if i+1 == len(regex):
                    return "/ operators nav atļauts beigās, lietojiet '//', lai burtiski prasītu '/'!"
                literal = False
                lastalpha = True
                lastOpenParenthesis = False
                conjLast = False
                groupModLast = False
                
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
                groupModLast = False    
            elif c == '(':
                lastOpenParenthesis = True
                lastalpha = False 
                stack.append(i)
                conjLast = False
                groupModLast = False
                
            elif c == ')':
                if lastOpenParenthesis or groupModLast:
                    return f"Tukšas iekavas {i} pozīcijā"
                isFirstGroup = False    
                lastalpha == True
                if len(stack) == 0:
                    return f"Iekava ) {i} pozīcijā neko neaizver"
                stack.pop()
                lastOpenParenthesis = False
                groupModLast = False
                
            elif c == '|':
                conjLast = True
                conjInd = i
                if not lastalpha:
                    return f"| pozīcijā {i} ir neatļauts"
                lastalpha = False 
                lastOpenParenthesis = False
                groupModLast = False
                
            elif c == '*':
                if not lastalpha:
                    return f"* pozīcijā {i} ir neatļauts"
                lastalpha = False 
                lastOpenParenthesis = False
                groupModLast = False
                
            elif c == '/':
                literal = True
            elif c == '?':
                incorrectUseError = f"pozīcijā {i} '?' nav atļauts, lai burtiski atrast '?', lietojiet '/?'"
                if not lastOpenParenthesis:
                    return incorrectUseError
                
                if i+1 != len(regex):

                    if regex[i+1] == '<':
                        if i+2 == len(regex) or regex[i+2] not in {'!', '='}:
                            return incorrectUseError
                        lookAhead = False
                        i+=2                 
                    elif regex[i+1] in {'!', '=', ':'}:
                        lookAhead = True
                        i+=1
                    else:
                        return incorrectUseError

                    if regex[i] != ':':
                        if lookAhead:
                           lastGroupReq = True
                        elif not isFirstGroup:
                            return f"Pozīcijā {i} neatļauta atpakaļškatīšanās. Atļauts tikai izteiksmes sākumā."
                              

                groupModLast = True
                
                lastOpenParenthesis = False
                conjLast = False
                groupModLast = False

            else:
                lastalpha = True
                lastOpenParenthesis = False
                conjLast = False
                groupModLast = False
                
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
    def __compileNFA(self, regex : str, ind = 1, groupId = 0):
        '''
        Izveido nedeterminētu automātu no regex jeb tādu, 
        kuram var būt vairāki ceļi no vienas ievades
        Nepieciešams, lai izveidotu pilno automātu

        ind ir nākamais indekss jaunam stāvoklim
        groupId ir nākamais stāvoklis jaunai nenosauktai grupai

        Atgriež : automāta pārejas, akceptējošo stāvokli, nākamo indeksu, vai radītais automāts akceptē tukšumu, 
                    notverošās grupas ({nosaukums : {start_1, start_2 ,..., start_n}, {accepting_1, accepting_2 ,..., accepting_n}])}),
                    nākamo nenosauktās grupas nosaukumu
        '''
            
        regex = regex.replace(" ", "") # Neņem vērā atstarpes jeb 'A | B' = 'A|B'
       
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
            if c == '\\' and pos+1 != len(regex) and regex[pos+1] == 's':
                c = " "
                pos+=1
            elif c == "$":
                c = '\n'
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
                if regex[pos+1] == '?': #netveroša izteiksme
                    if regex[pos+2] == ':':
                        pos += 2
                        nextCaptureName = None     
                elif regex[pos+1] == '<': #grupa ar nosaukumu
                    end = regex.find('>', pos+2)
                    nextCaptureName = regex[pos+2:end]
                    pos += len(nextCaptureName) + 2
                else:
                    nextCaptureName = str(groupId)
                    groupId+=1

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
                skip = self.__mathchingParenthesesIndex(regex, pos)
                subStart = ind
                substr = regex[pos+1:skip]
                sub, suba, ind, conjoptional, subCaptuingGroups, groupId = self.__compileNFA(substr, ind = ind+1, groupId=groupId)

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
                for cgname, (starts, ends) in subCaptuingGroups.items():
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

        return NFA, accepting1, ind, optionalsub, capturingGroups, groupId   

    def __mathchingParenthesesIndex(self, string, open):
            '''
            Atrod indeksu iekavai, kas aizver iekavu open indeksā string virknē
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

    def __mathchingParenthesesIndex2(self, string, closed):
        '''
        Atrod indeksu iekavai, kas atver iekavu closed indeksā string virknē 
        Ja nav atgriež -1
        '''
        closeCount = 1
        prevClose = False
        prevOpen = False
        for i in reversed(range(closed)):

            if string[i] == '/':
                if prevClose:
                    closeCount-=1
                    if closeCount==0:
                        return -1
                elif prevOpen:
                    closeCount+=1

            prevOpen = False
            prevClose = False   

            if string[i] == "(":
                closeCount-=1
                if closeCount==0:
                    return i
                prevOpen = True
            elif string[i] == ")":    
                closeCount+=1
                prevClose = True
     
        return -1         

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
    #regex = Regex('(<number>(1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*)', checkForErrors=False)
    #regex.saveVisualAutomata("C:/Temp")
    #print(regex.replace("8 234 918", "({number})", groupFunctions={"number" : lambda n : str(int(n)*12) }))
    # regex = Regex("(?:A)(B|C)", checkForErrors=False)
    # print(list(regex.find("BAB")))
    # regex = Regex("(?:A)(<grupa>A)", checkForErrors=False)
    # print(list(regex.find("AAC", coverAllow=True)))
    # regex = Regex("(<HG>A)(G)(?!4)", checkForErrors=False)
    # print(list(regex.find("AG4AGAG4")))
    # regex = Regex("www/.(..*)/.((?:com)|(?:net)|(?:gov))(?=,|\s|$)")
    # regex.lookahead.saveVisualAutomata("C:/Temp")
    # print(regex.replace("""www.home.net is a great site, but also there is 
    #                      www..com which does not exist. Make sure to visit www.schools.gov,
    #                      but also don't forget www.test.com
    #  """, "(Site name: {}, domain : {})"))
    pass

if __name__ == "__main__":
    main()








