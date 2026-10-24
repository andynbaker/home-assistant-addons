FROM mbentley/omada-controller:3.2
COPY addon-entrypoint.sh /addon-entrypoint.sh
RUN chmod 755 /addon-entrypoint.sh
ENTRYPOINT ["/addon-entrypoint.sh"]
# CMD is inherited from mbentley's image.
