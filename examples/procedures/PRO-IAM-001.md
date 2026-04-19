# PRO-IAM-001 — Gestión del ciclo de vida de cuentas de usuario

**Versión**: 1.2
**Aprobado por**: CISO
**Fecha de revisión**: 2025-01-15
**Clasificación**: Interno

---

## 1. Objetivo

Garantizar que el acceso a los sistemas de información se concede, modifica y revoca
de forma controlada y trazable, de acuerdo con el principio de mínimo privilegio.

## 2. Alcance

Aplica a todas las cuentas de usuario en sistemas de la organización, incluyendo
cuentas de dominio Active Directory, accesos a aplicaciones SaaS y accesos a
infraestructura cloud (AWS, Azure, GCP).

## 3. Procedimiento de alta de usuarios

3.1. Toda solicitud de alta de usuario debe tramitarse mediante el formulario FRM-IAM-001
     y contar con la aprobación del responsable de área.

3.2. El departamento de IT crea la cuenta en un plazo máximo de 2 días hábiles desde
     la recepción del formulario aprobado.

3.3. Se asigna el perfil de acceso mínimo necesario para el desempeño de las funciones.

## 4. Procedimiento de baja y cuentas inactivas

**4.1.** Cuando un empleado causa baja en la organización, su cuenta se desactiva
        **el mismo día** de la baja efectiva. En ningún caso se mantendrá activa
        más de 24 horas tras la baja.

**4.2.** Las cuentas sin actividad durante más de **30 días** se desactivan
        automáticamente mediante tarea programada en Active Directory.

**4.3.** Las cuentas con privilegios de administrador sin actividad durante más de
        **15 días** se desactivan y se notifica al CISO.

**4.4.** Las cuentas desactivadas se eliminan definitivamente tras **90 días** de
        inactividad, previa revisión del responsable de área.

## 5. Revisión periódica de accesos

5.1. El responsable de cada área revisará trimestralmente los accesos de su equipo
     y confirmará o revocará los que ya no sean necesarios.

5.2. El departamento de IT generará un informe mensual de cuentas inactivas para
     revisión del CISO.

## 6. Control de accesos privilegiados

6.1. Los accesos de administrador se gestionan mediante el sistema PAM (Privileged
     Access Management) y requieren aprobación del CISO para su concesión.

6.2. Los administradores utilizarán cuentas separadas para operaciones privilegiadas,
     nunca sus cuentas de usuario habituales.

## 7. Sanciones

El incumplimiento de este procedimiento puede derivar en medidas disciplinarias
de acuerdo con el Reglamento Interno de la organización.

---

**Controles normativos asociados**:
- ISO 27001:2022 A.5.18 (Derechos de acceso)
- ISO 27001:2022 A.5.15 (Control de acceso)
- ENS op.acc.4 (Proceso de gestión de derechos de acceso)
- ENS org.4 (Proceso de autorización)
