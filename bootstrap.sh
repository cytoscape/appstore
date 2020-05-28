#!/usr/bin/env bash

# update apt database
apt-get update

# install base packages
apt-get -y install apache2 apache2-dev apache2-utils ssl-cert wget
apt-get -y install libapache2-mod-wsgi-py3 gcc g++
apt-get -y install mysql-server
apt-get -y install libjpeg8-dev

# not sure if this is needed anymore
apt-get -y install geoip-database

# install miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod a+x Miniconda3-latest-Linux-x86_64.sh

./Miniconda3-latest-Linux-x86_64.sh -p /opt/miniconda3 -b
rm ./Miniconda3-latest-Linux-x86_64.sh

# set path to miniconda -- should really add to /etc/profile.d so everyone gets it
export PATH=/opt/miniconda3/bin:$PATH
echo "export PATH=/opt/miniconda3/bin:$PATH" >> /root/.bash_profile
echo "export PATH=/opt/miniconda3/bin:$PATH" >> /root/.bashrc
sudo -u vagrant echo "export PATH=/opt/miniconda3/bin:$PATH" >> /home/vagrant/.bash_profile

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

# for code coverage
pip install coverage

# create database
mysqladmin create AppStore

dbpass=`uuidgen`
cat /vagrant/createdb.sql | sed "s/@@PASSWORD@@/$dbpass/g" > /tmp/createdb.sql

mysql -u root < /tmp/createdb.sql

# TODO get app working properly
cd /var/www
mkdir CyAppStore
cd CyAppStore
cp -a /vagrant/* .
mkdir logs
mkdir media

# update the database password
sed -i "s/@@PASSWORD@@/$dbpass/g" /var/www/CyAppStore/settings.py

rm /var/www/CyAppStore/appstore.http.conf
rm /var/www/CyAppStore/appstore.include.conf

cd /var/www/CyAppStore

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

# fix permissions
chown -R www-data:www-data /var/www
find /var/www -type d -exec chmod 2750 {} \+
find /var/www -type f -exec chmod 640 {} \+

# Replace default site configuration
mkdir /etc/apache2/includes
cp /vagrant/appstore.include.conf /etc/apache2/includes/.
cp /vagrant/appstore.http.conf /etc/apache2/sites-available/appstore.conf
echo "Listen 8080" >> /etc/apache2/ports.conf
a2dissite 000-default.conf
a2ensite appstore.conf


# Reload apache
systemctl reload apache2

echo ""
echo "Visit http://localhost:8080"
