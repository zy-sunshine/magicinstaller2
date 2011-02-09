import gettext
cat = gettext.GNUTranslations(open("messages.mo"))
_ = cat.gettext
print _("Exit")
print _("Backup Files")
