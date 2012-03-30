#!/usr/bin/python
from miui import _
from miui.utils import magicstep, magicpopup
from xml.dom.minidom import parseString
class MIStep_accounts (magicstep.magicstepgroup):
    class account_dialog (magicpopup.magicpopup):
        def __init__(self, uixml, stepobj):
            magicpopup.magicpopup.__init__(self, stepobj, uixml, _('Add/Edit a user'),
                                           magicpopup.magicpopup.MB_OK |
                                           magicpopup.magicpopup.MB_CANCEL,
                                           'account.dialog')
            self.fill_values(stepobj.tmpvalues)

    def __init__(self, rootobj):
        self.origdoc = parseString("""<?xml version="1.0"?>
<tmpvalues>
<username/><password/><confirm_password/><shell/>
<homedir>false</homedir><customhomedir/>
<uid>false</uid><customuid>500</customuid>
</tmpvalues>""")
        self.accdlg = None
        magicstep.magicstepgroup.__init__(self, rootobj, 'accounts.xml',
                                          ['root', 'others'], 'step')
        self.tmpvalues = None

    def get_label(self):
        return  _("Accounts & hostname")

    def check_leave_root(self):
        self.fetch_values(self.rootobj.values)
        rootpwd = self.get_data(self.values, 'accounts.root.password')
        rootpwdconfirm = self.get_data(self.values, 'accounts.root.passwordconfirm')
        if rootpwd != rootpwdconfirm:
            magicpopup.magicmsgbox(None,
                                   _('Your root password is different with your root password confirmation!'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicmsgbox.MB_OK)
            return 0
        if len(rootpwd) < 3:
            magicpopup.magicmsgbox(None,
                                   _('Please do not use the password which shorter than 3 characters.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicmsgbox.MB_OK)
            return 0
        return 1

    def check_leave_others(self):
        self.fetch_values(self.rootobj.values)
        ulnode = self.srh_data_node(self.values, 'accounts.userlist')
        all_username = {}
        all_uid = {}
        for rownode in ulnode.getElementsByTagName('row'):
            username = rownode.getAttribute('c0')
            if all_username.has_key(username):
                # TO TRANSLATOR: Do not translate %FIRST.
                errtxt = _("Two user share the same username '%s'.")
                errtxt = errtxt % username
                magicpopup.magicmsgbox(None, errtxt,
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicmsgbox.MB_OK)
                return 0
            all_username[username] = 'y'
            uid = rownode.getAttribute('c4')
            if uid == 'Auto':
                continue
            if all_uid.has_key(uid):
                errtxt = _("The custom uid is conflict between '%s' and '%s'.")
                errtxt = errtxt % (all_uid[uid], rownode.getAttribute('c0'))
                magicpopup.magicmsgbox(None, errtxt,
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicmsgbox.MB_OK)
                return 0
            all_uid[uid] = rownode.getAttribute('c0')
        return 1

    def add_user(self, widget, data):
        self.tmpdoc = self.origdoc.cloneNode(8)
        self.tmpvalues = self.tmpdoc.documentElement
        self.iter = None  # It is an add.
        self.accdlg = self.account_dialog(self.uixmldoc, self)

    def edit_user(self, widget, data):
        self.tmpdoc = self.origdoc.cloneNode(8)
        self.tmpvalues = self.tmpdoc.documentElement
        (model, self.iter) = self.name_map['userlist_treeview'].get_selection().get_selected()
        if self.iter:
            username = model.get_value(self.iter, 0)
            self.set_data(self.tmpdoc, 'username', username)
            value = model.get_value(self.iter, 1)
            self.set_data(self.tmpdoc, 'password', value)
            self.set_data(self.tmpdoc, 'confirm_password', value)
            self.set_data(self.tmpdoc, 'shell', model.get_value(self.iter, 2))
            homedir = model.get_value(self.iter, 3)
            if homedir == '/home/' + username:
                self.set_data(self.tmpdoc, 'homedir', 'false')
                self.set_data(self.tmpdoc, 'customhomedir', '')
            else:
                self.set_data(self.tmpdoc, 'homedir', 'true')
                self.set_data(self.tmpdoc, 'customhomedir', homedir)
            uid = model.get_value(self.iter, 4)
            if uid == _('Auto'):
                self.set_data(self.tmpdoc, 'uid', 'false')
                self.set_data(self.tmpdoc, 'customuid', '500')
            else:
                self.set_data(self.tmpdoc, 'uid', 'true')
                self.set_data(self.tmpdoc, 'customuid', str(uid))
        self.accdlg = self.account_dialog(self.uixmldoc, self)

    def remove_user(self, widget, data):
        iter = self.name_map['userlist_treeview'].get_selection().get_selected()
        if iter[1]:
            self.list_remove('accounts.userlist', iter[1])
        else:
            magicpopup.magicmsgbox(None,
                                   _('Please choose a user to remove.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicmsgbox.MB_OK)

    def ok_clicked(self, widget, data):
        self.accdlg.fetch_values(self.tmpdoc)
        username = self.get_data(self.tmpvalues, 'username')
        if username == '':
            magicpopup.magicmsgbox(None,
                                   _('Username is not specified.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicmsgbox.MB_OK)
            return
        password = self.get_data(self.tmpvalues, 'password')
        confirmpassword = self.get_data(self.tmpvalues, 'confirm_password')
        if password != confirmpassword:
            magicpopup.magicmsgbox(None,
                                   _('Your password is different with your confirm password.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicmsgbox.MB_OK)
            return
        if password == '':
            magicpopup.magicmsgbox(None,
                                   _('You can not login in this user directly because you leave the password to blank'),
                                   magicpopup.magicmsgbox.MB_WARNING,
                                   magicpopup.magicmsgbox.MB_OK)
        self.accdlg.topwin.destroy()
        shell = self.get_data(self.tmpvalues, 'shell')
        homedir = self.get_data(self.tmpvalues, 'homedir')
        if homedir == 'true':
            homedir = self.get_data(self.tmpvalues, 'customhomedir')
        else:
            homedir = '/home/' + username
        uid = self.get_data(self.tmpvalues, 'uid')
        if uid == 'true':
            uid = str(int(float(self.get_data(self.tmpvalues, 'customuid'))))
        else:
            uid = _('Auto')
        newrow = self.rootobj.values.createElement('row')
        newrow.setAttribute('c0', username)
        newrow.setAttribute('c1', password)
        newrow.setAttribute('c2', shell)
        newrow.setAttribute('c3', homedir)
        newrow.setAttribute('c4', uid)
        if self.iter:
            self.list_replace('accounts.userlist', self.iter, newrow)
        else:
            self.list_append('accounts.userlist', newrow)
