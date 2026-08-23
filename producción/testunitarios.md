# Pruebas Unitarias - Guia para Principiantes

## Para que existen las pruebas unitarias?

**Imagina esto:**

```
Tu tienes una funcion que calcula el precio final de un producto
Un dia la modificas
Ahora todos los precios salen mal
No sabes que cambiaste
Tienes que revisar TODO manualmente
```

**Con pruebas unitarias:**

```
Tu tienes una funcion que calcula el precio final
Escribiste una prueba que verifica: "el precio debe ser 1150 con 15% de impuesto"
Modificas la funcion
Ejecutas la prueba
Si falla, SABES exactamente que se rompio
```

## Que es una prueba unitaria?

Es **verificar que UNA FUNCION haga lo que debe hacer**.

```python
# Tu funcion
def calcular_precio(precio, impuesto):
    return precio * (1 + impuesto)

# Tu prueba unitaria
def test_calcular_precio():
    resultado = calcular_precio(1000, 0.15)
    assert resultado == 1150
```

**Unitaria** significa: **una cosa a la vez**.

## La mentalidad correcta

### Preguntate esto antes de escribir cada prueba

```
1. Que hace esta funcion?
2. Que le paso como entrada?
3. Que debo esperar como salida?
4. Que pasa si le doy algo invalido?
```

### Ejemplo real

```python
# Funcion a probar
def calcular_descuento(precio, porcentaje):
    if porcentaje < 0 or porcentaje > 100:
        raise ValueError("Porcentaje invalido")
    return precio * (1 - porcentaje / 100)

# Preguntas:
# 1. Que hace? Calcula el precio con descuento
# 2. Entrada? Precio y porcentaje
# 3. Salida? Precio con descuento aplicado
# 4. Invalido? Si porcentaje es menor a 0 o mayor a 100
```

## Como empezar: el proceso paso a paso

### Paso 1: Entender la funcion

Antes de escribir nada, lee la funcion:

```python
def calcular_precio_total(items):
    total = 0
    for item in items:
        total += item["precio"] * item["cantidad"]
    return total
```

Preguntate:
- Que recibe? Una lista de items
- Que hace? Suma el precio de cada item multiplicado por su cantidad
- Que devuelve? Un numero (el total)

### Paso 2: Identificar los casos normales

Que es lo que **deberia funcionar**?

```python
# Caso normal: 2 items
items = [
    {"precio": 100, "cantidad": 2},
    {"precio": 50, "cantidad": 3}
]
# 100*2 + 50*3 = 200 + 150 = 350
```

### Paso 3: Identificar los casos extremos

Que pasa con situaciones **poco comunes pero validas**?

```python
# Lista vacia
items = []

# Un solo item
items = [{"precio": 100, "cantidad": 1}]

# Items con cantidad 1
items = [{"precio": 100, "cantidad": 1}]
```

### Paso 4: Identificar los casos de error

Que pasa si algo **esta mal**?

```python
# Precio negativo
items = [{"precio": -100, "cantidad": 1}]

# Cantidad cero
items = [{"precio": 100, "cantidad": 0}]

# Lista None
items = None
```

### Paso 5: Escribir las pruebas

```python
import pytest

def test_calcular_total_items_normales():
    """Test con items normales."""
    items = [
        {"precio": 100, "cantidad": 2},
        {"precio": 50, "cantidad": 3}
    ]
    assert calcular_precio_total(items) == 350

def test_calcular_total_lista_vacia():
    """Test con lista vacia."""
    items = []
    assert calcular_precio_total(items) == 0

def test_calcular_total_un_solo_item():
    """Test con un solo item."""
    items = [{"precio": 100, "cantidad": 1}]
    assert calcular_precio_total(items) == 100
```

## Los 5 tipos de pruebas unitarias que necesitas

### 1. Prueba de exito (Happy Path)

**Que pasa cuando todo va bien.**

```python
def test_sumar():
    assert sumar(2, 3) == 5
```

### 2. Prueba de limite

**Que pasa con los valores extremos validos.**

```python
def test_edad_minima():
    assert validar_edad(0) == True

def test_edad_maxima():
    assert validar_edad(150) == True
```

### 3. Prueba de error

**Que pasa cuando algo esta mal.**

```python
def test_edad_negativa():
    with pytest.raises(ValueError):
        validar_edad(-1)
```

### 4. Prueba de estado vacio

**Que pasa cuando no hay datos.**

```python
def test_lista_vacia():
    assert procesar([]) == []
```

### 5. Prueba de valores por defecto

**Que pasa cuando no se pasan todos los parametros.**

```python
def test_configuracion_default():
    config = crear_configuracion()
    assert config["timeout"] == 30
```

## Que NO debes probar (y por que)

### No pruebes codigo trivial

```python
# NO necesitas probar esto
def test_sumar():
    assert 1 + 1 == 2

# Es solo una suma, no tiene logica
```

### No pruebes getters y setters simples

```python
# NO necesitas probar esto
def test_get_nombre():
    usuario = Usuario("Jair")
    assert usuario.nombre == "Jair"

# Es solo acceder a un atributo
```

### No pruebes implementacion, prueba comportamiento

```python
# MAL: pruebas como esta implementada
def test_usa_lista_interna():
    procesador = Procesador()
    procesador.agregar("item")
    assert "item" in procesador._items_internos  # Pruebas implementacion

# BIEN: pruebas que hace
def test_procesar_items():
    procesador = Procesador()
    procesador.agregar("item")
    resultado = procesador.procesar()
    assert resultado == "item procesado"  # Pruebas comportamiento
```

### No pruebes dependencias externas

```python
# MAL: depende de API externa
def test_api_clima():
    clima = obtener_clima("CDMX")
    assert clima["temperatura"] > 0

# BIEN: mock la dependencia
def test_api_clima_mock():
    with patch('requests.get') as mock:
        mock.return_value.json.return_value = {"temperatura": 25}
        clima = obtener_clima("CDMX")
    assert clima["temperatura"] == 25
```

## Como pensar en cada prueba

### Antes de escribir

```
1. Que hace la funcion?
2. Que debo pasarle?
3. Que debo recibir?
4. Que pasa si algo esta mal?
```

### Despues de escribir

```
1. La prueba es clara?
2. El nombre describe que hace?
3. Es independiente de otras pruebas?
4. Es rapida?
```

## Ejemplo real: DocChat

### Funcion a probar

```python
# En retriever/builder.py
def build_hybrid_retriever(docs):
    """Construye un retriever hibrido."""
    # Crea vector store con ChromaDB
    # Crea BM25 retriever
    # Combina ambos
    return hybrid_retriever
```

### Pruebas unitarias

```python
# tests/unit/test_retriever.py

def test_build_retriever_con_documentos():
    """Test que el retriever se construye con documentos."""
    docs = ["documento de prueba"]
    retriever = build_hybrid_retriever(docs)
    assert retriever is not None

def test_build_retriever_sin_documentos():
    """Test que falla con lista vacia."""
    with pytest.raises(ValueError):
        build_hybrid_retriever([])
```

## La regla de oro

**Si puedes explicar en una oracion que hace la prueba, esta bien escrita.**

```python
# BIEN
def test_calcular_precio_con_impuesto():
    """Verifica que calcular_precio suma el 15% de impuesto."""
    assert calcular_precio(1000, 0.15) == 1150

# MAL
def test_funcion():
    """Test."""
    assert calcular_precio(1000, 0.15) == 1150
```

## Resumen: como empezar

```
1. Lee la funcion que vas a probar
2. Preguntate: que hace, que recibe, que devuelve
3. Piensa en casos normales
4. Piensa en casos extremos
5. Piensa en casos de error
6. Escribe una prueba para cada caso
7. Verifica que las pruebas pasan
8. Ejecuta pytest
```

## Ejercicio practice

Toma una funcion de tu proyecto y:

```
1. Lee la funcion
2. Identifica 3 casos normales
3. Identifica 1 caso extremo
4. Identifica 1 caso de error
5. Escribe 5 pruebas unitarias
6. Ejecuta pytest
```

## Siguiente paso

Una vez que entiendas esto, pasamos a:
- **Pruebas de integracion**: Probar como trabajan juntos
- **Fixtures**: Datos de prueba reutilizables
- **Mocking**: Simular dependencias externas
