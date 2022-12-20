import unittest as ut
from regexautomata2 import Regex

class Test_AcceptTest(ut.TestCase):
    def test_accept1(self):
        r = Regex("AB")
        self.assertTrue(r.isAccepted("AB"))
        self.assertFalse(r.isAccepted("ABC"))

    def test_accept2(self):
        r = Regex("AB*")
        self.assertTrue(r.isAccepted("ABB"))
        self.assertTrue(r.isAccepted("A"))
        self.assertFalse(r.isAccepted("ABBA"))

    def test_accept3(self):
        r = Regex("A|B")
        self.assertTrue(r.isAccepted("A"))
        self.assertTrue(r.isAccepted("B"))
        self.assertFalse(r.isAccepted("G"))
        self.assertFalse(r.isAccepted("AB"))

    def test_accept4(self):
        r = Regex("(AB)(VB)")
        self.assertTrue(r.isAccepted("ABVB"))
        self.assertFalse(r.isAccepted("ABAB"))
    
    def test_accept10(self):
        r = Regex("(AB)|(VB)")
        self.assertTrue(r.isAccepted("AB"))
        self.assertTrue(r.isAccepted("VB"))
        self.assertFalse(r.isAccepted("ABVB"))
        self.assertFalse(r.isAccepted(""))
    
    def test_accept11(self):
        r = Regex("%|(B)")
        self.assertTrue(r.isAccepted(""))

    def test_accept5(self):
        from regexautomata2 import Regex
        r = Regex("(AB)*V*|(BH)")
        self.assertTrue(r.isAccepted("ABABABBH"))
        self.assertTrue(r.isAccepted("ABABABVVVV"))
        self.assertTrue(r.isAccepted("ABABAB"))
        self.assertTrue(r.isAccepted(""))
        self.assertTrue(r.isAccepted("VVV"))
        
        self.assertFalse(r.isAccepted("ACV"))
        self.assertFalse(r.isAccepted("ABVBH"))    
        self.assertFalse(r.isAccepted("BHV"))

    def test_accept6(self):
        r = Regex("AV|%")
        self.assertTrue(r.isAccepted("AV"))
        self.assertTrue(r.isAccepted("A"))
        
        self.assertFalse(r.isAccepted("V"))
        self.assertFalse(r.isAccepted(""))

    def test_accept7(self):
        r = Regex("%|H")
        self.assertTrue(r.isAccepted(""))
        self.assertTrue(r.isAccepted("H"))
        
        self.assertFalse(r.isAccepted("HH"))

    def test_accept8(self):
        r = Regex("J.*GU|.")
        self.assertTrue(r.isAccepted("JGU"))
        self.assertTrue(r.isAccepted("JGI"))
        self.assertTrue(r.isAccepted("JHKLGI"))
        
        self.assertFalse(r.isAccepted("JHKLI"))
        self.assertFalse(r.isAccepted("JHKLG"))  

    def test_accept9(self):
        r = Regex("A/.B")
        self.assertTrue(r.isAccepted("A.B"))

        self.assertFalse(r.isAccepted("AHB"))  
    
    def test_accept11(self):
        r = Regex("(AB)+")
        self.assertTrue(r.isAccepted("ABABAB"))

        self.assertFalse(r.isAccepted(""))  

    def test_accept12(self):
        r = Regex("AB+")
        self.assertTrue(r.isAccepted("ABBBBB"))

        self.assertFalse(r.isAccepted("A")) 

    def test_accept13(self):
        r = Regex("(\w+\d+)*")
        self.assertTrue(r.isAccepted("AFFAD837892137"))
        self.assertTrue(r.isAccepted("AFF5424ADSF435"))
        self.assertTrue(r.isAccepted(""))

        self.assertFalse(r.isAccepted("A"))
        self.assertFalse(r.isAccepted("A52T"))                   
        
class Test_ReplaceTest(ut.TestCase):
    def test_accept1(self):
        r = Regex("(\\d|\\w)*\\d(\\d|\\w)*")
        self.assertEqual(r.replace("gh32 afsdg 14 nif ija3 0asf", "found"),
        "found afsdg found nif found found")
    
    def test_accept2(self):
        r = Regex("\\w+(\\s|,)+\\w+$")
        self.assertEqual(r.replace("text text more, text", "found"),
        "text text found")
    
    def test_accept3(self):
        from regexautomata2 import Regex
        r = Regex("\\w+abc(?=\\s|$)")
        print(r.lookahead.isAccepted(""))
        self.assertEqual(r.replace("faffabc fsdf shffab sdafabc", "found"),
        "found fsdf shffab found")

    def test_accept4(self):
        r = Regex("([0-9a-zA-Z.]+)@\w+/.com")
        self.assertEqual(r.replace("tim42@gmail.com raspberry john.smith@gmail.com www.google.com gmail.com", 
        "(name : {0})"),
        "(name : tim42) raspberry (name : john.smith) www.google.com gmail.com")


if __name__ == '__main__':
    ut.main()