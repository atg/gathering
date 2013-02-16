import pip
from subprocess import call, check_call

foundinfi = False
for dist in pip.get_installed_distributions():
  n = dist.project_name
  if n == 'infi.recipe.application-packager':
    foundinfi = True
  if not foundinfi: continue
  if '.' in n or n.startswith("plone") or n.startswith("Products") or n.startswith("zope") or n.startswith("wicked"):
    continue
  try:
    check_call("pip install -U --no-deps '" + dist.project_name + "'", shell=True)
  except Exception as e:
    print 'HAD EXCEPTION: %s' % str(e)
  

