#!/usr/bin/env bash

# update apt database
dnf update

# install base packages
dnf install -y epel-release setroubleshoot wget httpd httpd-devel lsof unzip mysql-server mod_ssl python3-mod_wsgi openssl-devel bzip2-devel libffi-devel zlib-devel make libjpeg-turbo-devel gcc
dnf install -y certbot python3-certbot-apache


# install miniconda 3 with python 3.11
# to try newer versions just pick newer version of miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-py311_24.5.0-0-Linux-x86_64.sh
chmod a+x Miniconda*sh
./Miniconda*.sh -p /opt/miniconda3 -b

# set path to miniconda -- should really add to /etc/profile.d so everyone gets it
export PATH=/opt/miniconda3/bin:$PATH
echo "export PATH=/opt/miniconda3/bin:$PATH" >> /root/.bash_profile
echo "export PATH=/opt/miniconda3/bin:$PATH" >> /root/.bashrc
sudo -u vagrant echo "export PATH=/opt/miniconda3/bin:$PATH" >> /home/vagrant/.bash_profile

# install mysqlclient
conda install -y mysqlclient

# install mod_wsgi
pip install mod_wsgi

# following mod_wsgi instructions found here:
# https://ostrokach.gitlab.io/post/apache-django-anaconda/
#


# update wsgi.conf configuration
WSGI_CONF="/etc/httpd/conf.d/wsgi.conf"
SITE_PKG=`find /opt/miniconda3 -regex "/opt/miniconda3/lib/python.*/site-packages$" -type d 2> /dev/null`

echo "<IfModule !wsgi_module>" > $WSGI_CONF
echo "   WSGIPythonHome /opt/miniconda3" >> $WSGI_CONF
echo "   WSGIPythonPath $SITE_PKG" >> $WSGI_CONF
echo "</IfModule>" >> $WSGI_CONF


# update wsgi.load file
mod_wsgi-express install-module | egrep "^LoadModule" > /etc/httpd/conf.modules.d/10-wsgi-python3.conf


# updates shared library cache
ldconfig

pip install -r /vagrant/requirements.txt


# Ran into error when trying to call python manage.py scripts on 7-23-2021
#
#   File "/opt/miniconda3/lib/python3.9/site-packages/social_django/models.py", line 11, in <module>
#    from .storage import DjangoUserMixin, DjangoAssociationMixin, \
#  File "/opt/miniconda3/lib/python3.9/site-packages/social_django/storage.py", line 9, in <module>
#    from social_core.storage import UserMixin, AssociationMixin, NonceMixin, \
#  File "/opt/miniconda3/lib/python3.9/site-packages/social_core/storage.py", line 9, in <module>
#    from openid.association import Association as OpenIdAssociation
#  File "/opt/miniconda3/lib/python3.9/site-packages/openid/__init__.py", line 52, in <module>
#    if len(version_info) != 3:
# TypeError: object of type 'map' has no len()
#
# Found fix was to remove python-openid and python3-openid and install python3-openid again
#
pip uninstall python-openid -y
pip uninstall python3-openid -y

pip install python3-openid

# for code coverage
pip install coverage

# Enable and start mysql database
systemctl enable mysqld
systemctl start mysqld

# create database
mysqladmin create AppStore

dbpass=`uuidgen`
echo ""
echo "The database password will be set to: $dbpass"
echo "In case its need look at /tmp/createdb.sql"
echo ""
cat /vagrant/createdb.sql | sed "s/@@PASSWORD@@/$dbpass/g" > /tmp/createdb.sql

mysql -u root < /tmp/createdb.sql

APPSTORE="appstore"
cd /var/www
mkdir $APPSTORE
cd $APPSTORE
cp -a /vagrant/* .
mkdir logs
mkdir /var/www/html/media
mkdir /var/www/html/misc

cp /vagrant/favicon.ico /var/www/html/misc/.
cp /vagrant/google_oauth2_logo.png /var/www/html/misc/.

# update the database password
sed -i "s/@@PASSWORD@@/$dbpass/g" /var/www/$APPSTORE/settings/vagrant.py

# update wsgi
sed -i "s/settings.local/settings.vagrant/g" /var/www/$APPSTORE/wsgi.py

# update manage.py
sed -i "s/settings.local/settings.vagrant/g" /var/www/$APPSTORE/manage.py


rm /var/www/$APPSTORE/appstore.http.conf
rm /var/www/$APPSTORE/appstore.include.conf

cd /var/www/$APPSTORE

python manage.py makemigrations apps --noinput
python manage.py makemigrations backend --noinput
python manage.py makemigrations download --noinput
python manage.py makemigrations help --noinput
python manage.py makemigrations search --noinput
python manage.py makemigrations submit_app --noinput
python manage.py makemigrations users --noinput
python manage.py makemigrations --noinput

python manage.py migrate --noinput
python manage.py rebuild_index --noinput
python manage.py collectstatic --noinput

# fix permissions
chown -R apache:apache /var/www
find /var/www -type d -exec chmod 2750 {} \+
find /var/www -type f -exec chmod 640 {} \+

# Replace default site configuration
mkdir /etc/httpd/includes
cp /vagrant/appstore.include.conf /etc/httpd/includes/.
cp /vagrant/appstore.http.conf /etc/httpd/conf.d/appstore.conf

# update port to 8080 which needs to match forwarded port in Vagrantfile
sed -i "s/@@PORT@@/8080/g" /etc/httpd/conf.d/appstore.conf

# update ssl protocol
sed -i "s/@@SSLPROTOCOL@@/All -SSLv2 -SSLv3/g" /etc/httpd/conf.d/appstore.conf

# update ciphersuite
sed -i "s/@@SSLCIPHERSUITE@@/ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK/g" /etc/httpd/conf.d/appstore.conf

#
#sed -i "s/^.*SSLCertificateFile.*$/SSLCertificateFile      \/etc\/ssl\/certs\/ssl-cert-snakeoil.pem/g" /etc/httpd/conf.d/appstore.conf

#sed -i "s/^.*SSLCertificateKeyFile.*$/SSLCertificateKeyFile \/etc\/ssl\/private\/ssl-cert-snakeoil.key/g" /etc/httpd/conf.d/appstore.conf

#sed -i "s/^.*SSLCertificateChainFile.*$//g" /etc/httpd/conf.d/appstore.conf


echo "Listen 8080" > /etc/httpd/conf.d/ports.conf

setsebool -P httpd_can_network_connect 1
semanage fcontext -a -t httpd_sys_content_t '/var/www/appstore/wsgi.py'
semanage fcontext -a -t httpd_sys_content_t '/var/www/appstore/'
restorecon -Rv /var/www/appstore/

semanage fcontext -a -t httpd_sys_rw_content_t '/var/www/appstore/logs'
restorecon -v /var/www/appstore/logs
setsebool -P httpd_unified 1

# need to set a name for the server
echo "ServerName 127.0.0.1" >> /etc/httpd/conf/httpd.conf

# Reload apache
systemctl stop httpd
systemctl start httpd

echo ""
echo "Visit http://localhost:8080"
echo ""
echo "or to test vagrant ssh ; cd /var/www/$APPSTORE ; coverage run --source '.' manage.py test"
echo ""
