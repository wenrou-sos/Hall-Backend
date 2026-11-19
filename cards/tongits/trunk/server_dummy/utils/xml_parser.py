
from xml.dom import minidom

def Split(src, sep = ',', sep2 = None):
    if sep2 is None:
        rst = []
        if len(src) > 0:
            vSrcLst = src.split(sep)
            for i in range(len(vSrcLst)):
                rst.append(int(vSrcLst[i]))
        return rst
    else:
        rst = {}
        if len(src) > 0:
            vTmp = []
            vSrcLst = src.split(sep)
            for i in range(len(vSrcLst)):
                vTmp.append(vSrcLst[i])
            for i in range(len(vTmp)):
                vSrcLst2 = vTmp[i].split(sep2)
                if len(vSrcLst2) == 2:
                    rst[int(vSrcLst2[0])] = int(vSrcLst2[1])
        return rst

'''
# DOM
class XMLReader(object):
    @classmethod
    def GetNodes(cls, mNode, name):
        return mNode.getElementsByTagName(name)

    @classmethod
    def GetNode(cls, mNode, name):
        vNodes = mNode.getElementsByTagName(name)
        if len(vNodes) == 1:
            return vNodes[0]
        return None

    @classmethod
    def GetAttributeAsBool(cls, mNode, sAttr, bDef = False)->bool:
        if mNode.hasAttribute(sAttr):
            return int(mNode.getAttribute(sAttr)) == 1
        return bDef

    @classmethod
    def GetAttributeAsInt(cls, mNode, sAttr, nDef = 0)->int:
        if mNode.hasAttribute(sAttr):
            return int(mNode.getAttribute(sAttr))
        return nDef

    @classmethod
    def GetAttributeAsFloat(cls, mNode, sAttr, fDef = 0.0)->float:
        if mNode.hasAttribute(sAttr):
            return float(mNode.getAttribute(sAttr))
        return fDef

    @classmethod
    def GetAttributeAsIntList(cls, mNode, sAttr, sSep = ",", vDef = [])->list:
        if mNode.hasAttribute(sAttr):
            sNode = mNode.getAttribute(sAttr)
            if len(sNode) > 0:
                return Split(sNode, sSep)
        return vDef

    @classmethod
    def GetAttributeAsIntMap(cls, mNode, sAttr, sSep = ";", sSep2 = ",", dDef = {})->dict:
        if mNode.hasAttribute(sAttr):
            sNode = mNode.getAttribute(sAttr)
            if len(sNode) > 0:
                return Split(sNode, sSep, sSep2)
        return dDef
'''

class XMLReader(object):
    @classmethod
    def GetNodes(cls, mNode, name):
        return mNode.findall(name)

    @classmethod
    def GetNode(cls, mNode, name):
        return mNode.find(name)

    @classmethod
    def GetAttributeAsBool(cls, mNode, sAttr, bDef = False)->bool:
        value = mNode.get(sAttr, 0)
        if isinstance(value, int):
            return value == 1
        if isinstance(value, str):
            if len(value) == 0 or not str.isdigit(value):
                return nDef
            return int(value)==1
        return bDef

    @classmethod
    def GetAttributeAsInt(cls, mNode, sAttr, nDef = 0)->int:
        value = mNode.get(sAttr, nDef)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if len(value) == 0 or not str.isdigit(value):
                return nDef
            return int(value)
        return nDef

    @classmethod
    def GetAttributeAsFloat(cls, mNode, sAttr, fDef = 0.0)->float:
        value = mNode.get(sAttr, fDef)
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            if len(value) == 0:# or not str.isdigit(value):
                return fDef
            return float(value)
        return fDef

    @classmethod
    def GetAttributeAsIntList(cls, mNode, sAttr, sSep = ",", vDef = [])->list:
        sNode = str(mNode.get(sAttr, ""))
        if len(sNode) > 0:
            return Split(sNode, sSep)
        return vDef

    @classmethod
    def GetAttributeAsIntMap(cls, mNode, sAttr, sSep = ";", sSep2 = ",", dDef = {})->dict:
        sNode = str(mNode.get(sAttr, ""))
        if len(sNode) > 0:
            return Split(sNode, sSep, sSep2)
        return dDef
