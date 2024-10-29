En este sistema, se van a utilizar los siguientes comandos para poder ejecutar los códigos de manera correcta: 

    git clone https://github.com/xfrogyzz/Tarea2_Sistemas_Distribuidos

    cd Tarea2_Sistemas_Distribuidos

Para levantar las imagenes docker se utiliza el siguiente comando.

    docker-compose up -d

En caso de que se quieran detener los servicios de Docker, se debe ejecutar el siguiente comando.

    docker-compose down

Luego, simultaneamente se deben ejecutar los siguientes códigos. 

    python Servidor.py

    python ClientegRPC.py

    python notificaciones.py

    python analisis.py

En el caso del ClientegRPC.py se deben ingresar los datos que se solicitan y posteriormente se puede ver como los servicios se van comunicando entre sí.
