FROM odoo:14.0
LABEL Siddhant Pageni. <siddhantpageni@gmail.com>

USER root
RUN mkdir -p /mnt/custom_addons

RUN apt-get update \
    && apt-get install

RUN chown -R odoo /mnt
RUN chown -R odoo /mnt/*