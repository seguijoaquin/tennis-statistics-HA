---
geometry: margin=2.5cm
title: Sistemas Distribuidos I
subtitle: Trabajo Práctico Final
documentclass: scrartcl
---



\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \  ![](diagramas/logo_fiuba.png) \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

\ \ \

**Alumnos**: Kevin Cajachuán (98725), Joaquín Seguí, Joaquín Torré Zaffaroni(98314)

**Materia**: Sistemas Distribuidos I, 75.74

**Cuatrimestre**: 2C2019

**Profesores**: Pablo D. Roca, Ezequiel Torres Feyuk


\newpage

## Introducción

Para el presente trabajo práctico se propone extender la funcionalidad del
trabajo práctico 2 incorporando nociones de tolerancia a fallos y manejo de
múltiples clientes. El resultado es, entonces, una arquitectura
distribuída orientada a _streaming_ utilizando _message oriented middlewares_
que soporta caídas de los procesos sin que ello afecte al resultado del cómputo.

El diseño de la arquitectura está orientado a un _pipeline_ con
unidades de cálculo ligadas al negocio, más otros procesos de soporte. En este
informe detallamos las decisiones detrás del diseño, documentamos la implementación
y marcamos puntos de mejora.



## Vista lógica

El DAG de este trabajo práctico es casi el mismo que el DAG del trabajo práctico 2
con la diferencia de que se agrega la etapa de filtrado del intervalo de fechas
en el que el cliente quiere que se haga el análisis. Por esta razón el cliente
le envía las líneas de los archivos al nuevo filtro y a partir de ahí, con las
líneas filtradas, se divide el procesamiento en 3 ramas:

1. Cálculo de porcentaje de victorias de zurdos sobre diestros y viceversa.
2. Partidos en los que el ganador tenía al menos 20 años más que el perdedor.
3. Cálculo del promedio de la duración en minutos de los partidos en cada superficie.

![](diagramas/DAG.png)

## Vista de desarrollo

Diagrama de paquetes


## Vista de proceso

### Esquema de multiprocesamiento

Comentar cómo se hizo

### Tolerancia a fallos

Para tolerancia a fallos utilizamos un proceso llamado __Watchdog__ que recibe
los _heartbeats_ de los demás procesos, y al detectar que uno se cayó los levanta
con la siguiente lógica:

![](diagramas/watchdog_spawner.png)

Sin embargo, el __Watchdog__ también puede fallar. Debido a eso, tenemos varias
instancias del nodo corriendo, solo uno en modo líder y el resto en modo _follower_.
Sólo el líder es el que escucha los _heartbeats_ y levanta los nodos.
Además, el líder manda sus propios _heartbeats_ al resto de los _followers_, de manera
de que éstos también puedan saber si se muere. En ese caso, se elige
un nuevo líder a través del algoritmo Bully.

![](diagramas/bully.png)


ídem

### Persistencia

ídem


![](diagramas/replicar_info.png)


Como el _master_ puede caerse, es necesario que otro nodo asuma el rol.
Para evitar tener que implementar de nuevo un algoritmo de elección
de líder, utilizamos el proceso __Watchdog__. En efecto, cada nodo
de almacenamiento agrega metadata a su _heartbeat_ con la información
del rol que cumple. Esta información es almacenada por el __Watchdog__
y esto le permite saber cuándo se cae el nodo maestro.

Entonces es necesario analizar el esquema de replicación teniendo en
cuenta las fallas de los nodos. En el caso de un esclavo que
se muere y luego se levanta, simplemente puede seguir leyendo
de su cola de Rabbit que es durable. Puede pasar que haya persistido
un dato y se haya caído antes de dar el `ACK`, pero como las
escrituras son _overwrites_ con _timestamps_ no es problema. Desde
el punto de vista del nodo maestro, si se cae antes de dar el `ACK`
el nuevo maestro puede recibir la misma escritura. Por la misma
razón que antes, esto no es problema.

A continuación se puede ver el diagrama que ilustra la
generación de un nuevo nodo maestro.

![](diagramas/nuevo_master.png)



## Vista física

Diagrama de despliegue

## Escenarios

Comentar los casos de prueba que tenemos en el doc de aceptación

## Conclusiones

Puntos de mejora

## Referencias

Coulouris, G. F., Dollimore, J., & Kindberg, T. (2005). Distributed systems: concepts and design. pearson education.

Apuntes de clase.
