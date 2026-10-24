FROM mbentley/omada-controller:3.2
COPY addon-entrypoint.sh /addon-entrypoint.sh
RUN chmod 755 /addon-entrypoint.sh
ENTRYPOINT ["/addon-entrypoint.sh"]
# Setting ENTRYPOINT clears the base CMD; restore the upstream v3 command.
CMD ["/opt/tplink/EAPController/jre/bin/java","-server","-Xms128m","-Xmx1024m","-XX:MaxHeapFreeRatio=60","-XX:MinHeapFreeRatio=30","-XX:+HeapDumpOnOutOfMemoryError","-XX:-UsePerfData","-Deap.home=/opt/tplink/EAPController","-cp","/opt/tplink/EAPController/lib/*:","com.tp_link.eap.start.EapLinuxMain"]
