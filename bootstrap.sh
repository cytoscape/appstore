#!/usr/bin/env bash

# update apt database
apt-get update

# install base packages
apt-get -y install apache2 apache2-dev apache2-utils ssl-cert wget unzip
apt-get -y install libapache2-mod-wsgi-py3 gcc g++
apt-get -y install mysql-server
apt-get -y install libjpeg8-dev

# not sure if this is needed anymore
apt-get -y install geoip-database

# install miniconda 3 with python 3.7
# to try newer versions just pick newer version of miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-py37_4.8.3-Linux-x86_64.sh
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
WSGI_CONF="/etc/apache2/mods-available/wsgi.conf"
SITE_PKG=`find /opt/miniconda3 -regex "/opt/miniconda3/lib/python.*/site-packages$" -type d 2> /dev/null`
echo "<IfModule mod_wsgi.c>" > $WSGI_CONF
echo "   WSGIPythonHome /opt/miniconda3" >> $WSGI_CONF
echo "   WSGIPythonPath $SITE_PKG" >> $WSGI_CONF
echo "</IfModule>" >> $WSGI_CONF

# update wsgi.load file
mod_wsgi-express install-module | egrep "^LoadModule" > /etc/apache2/mods-available/wsgi.load

# enable wsgi
a2enmod wsgi

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
chown -R www-data:www-data /var/www
find /var/www -type d -exec chmod 2750 {} \+
find /var/www -type f -exec chmod 640 {} \+

# Replace default site configuration
mkdir /etc/apache2/includes
cp /vagrant/appstore.include.conf /etc/apache2/includes/.
cp /vagrant/appstore.http.conf /etc/apache2/sites-available/appstore.conf

# update port to 8080 which needs to match forwarded port in Vagrantfile
sed -i "s/@@PORT@@/8080/g" /etc/apache2/sites-available/appstore.conf

# update ssl protocol
sed -i "s/@@SSLPROTOCOL@@/All -SSLv2 -SSLv3/g" /etc/apache2/sites-available/appstore.conf

# update ciphersuite
sed -i "s/@@SSLCIPHERSUITE@@/ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK/g" /etc/apache2/sites-available/appstore.conf

#
sed -i "s/^.*SSLCertificateFile.*$/SSLCertificateFile      \/etc\/ssl\/certs\/ssl-cert-snakeoil.pem/g" /etc/apache2/sites-available/appstore.conf

sed -i "s/^.*SSLCertificateKeyFile.*$/SSLCertificateKeyFile \/etc\/ssl\/private\/ssl-cert-snakeoil.key/g" /etc/apache2/sites-available/appstore.conf

sed -i "s/^.*SSLCertificateChainFile.*$//g" /etc/apache2/sites-available/appstore.conf

echo "Listen 8080" >> /etc/apache2/ports.conf
a2enmod ssl
a2dissite 000-default.conf
a2ensite appstore.conf


# Reload apache
systemctl reload apache2

echo ""
echo "Visit http://localhost:8080 or https://localhost:8443"
echo ""
echo "or to test vagrant ssh ; cd /var/www/$APPSTORE ; coverage run --source '.' manage.py test"
echo ""
