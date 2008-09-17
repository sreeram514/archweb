from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
import re

###########################
### User Profile Class ####
###########################
class UserProfile(models.Model):
    id = models.AutoField(primary_key=True) # not technically needed
    notify = models.BooleanField(
        "Send notifications",
        default=True,
        help_text="When enabled, send user 'flag out of date' notifications")
    alias = models.CharField(
        max_length=50,
        help_text="Required field")
    public_email = models.CharField(
        max_length=50,
        help_text="Required field")
    other_contact = models.CharField(max_length=100, null=True, blank=True)
    website = models.CharField(max_length=200, null=True, blank=True)
    yob = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    languages = models.CharField(max_length=50, null=True, blank=True)
    interests = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=50, null=True, blank=True)
    roles = models.CharField(max_length=255, null=True, blank=True)
    favorite_distros = models.CharField(max_length=255, null=True, blank=True)
    picture = models.FileField(upload_to='devs', default='devs/silhouette.png')
    user = models.ForeignKey(
        User, related_name='userprofile_user', unique=True)
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Additional Profile Data'
        verbose_name_plural = 'Additional Profile Data'


#######################
### Manager Classes ###
#######################
class TodolistManager(models.Manager):
    def get_incomplete(self):
        results = []
        for l in self.all().order_by('-date_added'):
            if TodolistPkg.objects.filter(list=l.id).filter(
                complete=False).count() > 0:
                results.append(l)
        return results

class PackageManager(models.Manager):
    def get_flag_stats(self):
        results = []
        # first the orphans
        noflag = self.filter(maintainer=0).count()
        flagged = self.filter(maintainer=0).filter(
                    needupdate=True).exclude(
                        repo__name__iexact='testing').count()
        results.append(
            (User(id=0,first_name='Orphans'), noflag, flagged))
        # now the rest
        for maint in User.objects.all().order_by('first_name'):
            noflag = self.filter(maintainer=maint.id).count()
            flagged = self.filter(maintainer=maint.id).filter(
                    needupdate=True).exclude(
                        repo__name__iexact='testing').count()
            results.append((maint, noflag, flagged))
        return results


#############################
### General Model Classes ###
#############################
class Mirror(models.Model):
    id = models.AutoField(primary_key=True)
    domain = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    protocol_list = models.CharField(max_length=255, null=True, blank=True)
    admin_email = models.CharField(max_length=255, null=True, blank=True)
    def __str__(self):
        return self.domain
    class Meta:
        db_table = 'mirrors'
    class Admin:
        list_display = ('domain', 'country')
        list_filter = ('country',)
        ordering = ['domain']
        search_fields = ('domain')
        pass

class Press(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'press'
        verbose_name_plural = 'press'
    class Admin:
        list_display = ('name', 'url')
        ordering = ['name']
        search_fields = ('name')
        pass

class AltForum(models.Model):
    id = models.AutoField(primary_key=True)
    language = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'alt_forums'
        verbose_name = 'AltForum'
    class Admin:
        list_display = ('language', 'name')
        list_filter = ('language',)
        ordering = ['name']
        search_fields = ('name')
        pass

class Donor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'donors'
    class Admin:
        ordering = ['name']
        search_fields = ('name')
        pass

class News(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User, related_name='news_author')
    postdate = models.DateField(auto_now_add=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    def __str__(self):
        return self.title
    class Meta:
        db_table = 'news'
        verbose_name_plural = 'news'
        get_latest_by = 'postdate'
        ordering = ['-postdate', '-id']

    def get_absolute_url(self):
        return '/news/%i/' % self.id

class Arch(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255,unique=True)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'arches'
        ordering = ['name']
        verbose_name_plural = 'arches'
    class Admin:
        pass

class Repo(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255,unique=True)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'repos'
        ordering = ['name']
        verbose_name_plural = 'repos'
    class Admin:
        pass

class Package(models.Model):
    id = models.AutoField(primary_key=True)
    repo = models.ForeignKey(Repo)
    arch = models.ForeignKey(Arch)
    maintainer = models.ForeignKey(User, related_name='package_maintainer')
    needupdate = models.BooleanField(default=False)
    pkgname = models.CharField(max_length=255)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    pkgdesc = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    last_update = models.DateTimeField(null=True, blank=True)
    objects = PackageManager()
    class Meta:
        db_table = 'packages'
        #get_latest_by = 'last_update'
        #ordering = ('-last_update',)

    class Admin:
        list_display = ('pkgname', '_reponame', '_archname', '_maintainername')
        list_filter = ('repo', 'arch', 'maintainer')
        ordering = ['pkgname']
        search_fields = ('pkgname',)
        pass

    def __str__(self):
        return self.pkgname

    # According to http://code.djangoproject.com/ticket/2583 we have "bad data"
    # The problem is the queries constructed by the admin  to retrieve foreign
    # keys are empty. This allows us to display items in the list but kills
    # sorting
    def _reponame(self):
        return self.repo.name
    _reponame.short_description='Repo'
    def _archname(self):
        return self.arch.name
    _archname.short_description='Arch'
    def _maintainername(self):
        return self.maintainer.username
    _maintainername.short_description = 'Maintainer'

    def get_absolute_url(self):
        return '/packages/%s/%s/%s/' % (self.repo.name.lower(),
                self.arch.name, self.pkgname)

    @property
    def signoffs(self):
        return Signoff.objects.filter(
            pkg=self,
            pkgver=self.pkgver,
            pkgrel=self.pkgrel)

    def approved_for_signoff(self):
        return self.signoffs.count() >= 2


    def get_requiredby(self):
        """
        Returns a list of package objects.
        """
        reqs = []
        requiredby = PackageDepend.objects.filter(depname=self.pkgname).filter(
            Q(pkg__arch=self.arch) | Q(pkg__arch__name__iexact='any'))
        for req in requiredby:
            reqs.append(req.pkg)
        ## sort the resultant list. Django has problems in the orm with
        ## trying to shoehorn the sorting into the reverse foreign key 
        ## reference in the query above. :(
        reqs.sort(lambda a,b: cmp(a.pkgname,b.pkgname))
        return reqs

    def get_depends(self):
        """
        Returns a list of tuples(3). 

        Each tuple in the list is one of:
         - (packageid, dependname, depend compare string) if a matching 
           package is found.
         - (None, dependname, None) if no matching package is found, eg 
           it is a virtual dep.
        """
        deps = []
        for dep in self.packagedepend_set.order_by('depname'):
            # we only need depend on same-arch-packages
            pkgs = Package.objects.filter(
                Q(arch__name__iexact='any') | Q(arch=self.arch),
                pkgname=dep.depname)
            if len(pkgs) == 0:
                # couldn't find a package in the DB
                # it should be a virtual depend (or a removed package)
                deps.append({'dep': dep, 'pkg': None})
                continue
            else:
                for pkg in pkgs:
                    deps.append({'dep': dep, 'pkg': pkg})
        return deps

class Signoff(models.Model):
    pkg = models.ForeignKey(Package)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    packager = models.ForeignKey(User)

class PackageFile(models.Model):
    id = models.AutoField(primary_key=True)
    pkg = models.ForeignKey('Package')
    path = models.CharField(max_length=255)
    class Meta:
        db_table = 'package_files'

class PackageDepend(models.Model):
    id = models.AutoField(primary_key=True)
    pkg = models.ForeignKey('Package')
    depname = models.CharField(db_index=True, max_length=255)
    depvcmp = models.CharField(max_length=255)
    class Meta:
        db_table = 'package_depends'

class Todolist(models.Model):
    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(User, related_name='todolist_creator')
    name = models.CharField(max_length=255)
    description = models.TextField()
    date_added = models.DateField(auto_now_add=True)
    objects = TodolistManager()
    def __str__(self):
        return self.name

    @property
    def packages(self):
        return TodolistPkg.objects.filter(list=self.id).order_by('pkg')

    @property
    def package_names(self):
        return '\n'.join(set([p.pkg.pkgname for p in self.packages]))

    class Meta:
        db_table = 'todolists'

class TodolistPkg(models.Model):
    id = models.AutoField(primary_key=True)
    list = models.ForeignKey('Todolist')
    pkg = models.ForeignKey('Package')
    complete = models.BooleanField(default=False)
    class Meta:
        db_table = 'todolist_pkgs'
        unique_together = (('list','pkg'),)

class Wikipage(models.Model):
    """Wiki page storage"""
    title = models.CharField(max_length=255)
    content = models.TextField()
    last_author = models.ForeignKey(User, related_name='wikipage_last_author')
    class Meta:
        db_table = 'wikipages'

    def editurl(self):
        return "/wiki/edit/" + self.title + "/"

    def __str__(self):
        return self.title

# vim: set ts=4 sw=4 et:

