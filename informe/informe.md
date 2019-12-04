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

**Alumnos**: Kevin Cajachuan (98725), Joaquín Seguí, Joaquín Torré Zaffaroni(98314)

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

Esta sección no cambia mucho, es el DAG.
Kevin: lo  que tenías del TP2 más si hiciste algún cambio.


## Vista de desarrollo

Diagrama de paquetes


## Vista de proceso

### Esquema de multiprocesamiento

Comentar cómo se hizo

### Tolerancia a fallos


![](diagramas/bully.png)


ídem

### Persistencia

ídem


## Vista física

Diagrama de despliegue

## Escenarios

Comentar los casos de prueba que tenemos en el doc de aceptación

## Conclusiones

Puntos de mejora

## Referencias

Coulouris, G. F., Dollimore, J., & Kindberg, T. (2005). Distributed systems: concepts and design. pearson education.

Apuntes de clase.