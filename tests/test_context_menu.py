import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from context_menu import install,uninstall,command_for,registry_keys,OWNER

class Handle:
    def __init__(self,store,key):self.store=store;self.key=key
    def __enter__(self):return self
    def __exit__(self,*args):pass
class Registry:
    HKEY_CURRENT_USER=1; REG_SZ=1
    def __init__(self):self.values={}
    def OpenKey(self,h,key):
        if key not in self.values:raise FileNotFoundError(key)
        return Handle(self.values,key)
    def CreateKey(self,h,key):self.values.setdefault(key,{});return Handle(self.values,key)
    def QueryValueEx(self,h,name):
        if name not in h.store[h.key]:raise FileNotFoundError(name)
        return h.store[h.key][name],1
    def SetValueEx(self,h,name,a,b,value):h.store[h.key][name]=value
    def DeleteKey(self,h,key):
        if key not in self.values:raise FileNotFoundError(key)
        del self.values[key]

class ContextMenuTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'Prism app';self.root.mkdir()
    def tearDown(self):self.tmp.cleanup()
    def files(self):
        exe=self.root/'.venv/Scripts/pythonw.exe';exe.parent.mkdir(parents=True);exe.touch();(self.root/'main.py').touch();return exe
    def test_install_remove_owned_keys(self):
        exe=self.files();reg=Registry();reg.values['unrelated']={'hello':'world'}
        install(reg,self.root)
        for key in registry_keys():
            self.assertEqual(reg.values[key]['PrismOwner'],OWNER)
            cmd=reg.values[key+'\\command'][''];self.assertEqual(cmd,command_for(exe,self.root/'main.py'))
            self.assertTrue(cmd.endswith('"%1"'));self.assertNotIn('cmd.exe',cmd)
        uninstall(reg);self.assertEqual(reg.values,{'unrelated':{'hello':'world'}})
    def test_missing_setup_no_mutation(self):
        r=Registry()
        with self.assertRaises(RuntimeError):install(r,self.root)
        self.assertFalse(r.values)
    def test_foreign_owner_not_overwritten(self):
        self.files();r=Registry();r.values[registry_keys()[0]]={'PrismOwner':'someone else'}
        with self.assertRaises(RuntimeError):install(r,self.root)
        self.assertEqual(len(r.values),1);uninstall(r);self.assertEqual(len(r.values),1)

if __name__=='__main__':unittest.main()
