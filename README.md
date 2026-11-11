# Своё приложение: ребрендинг проверенных клиентов

Здесь лежит «комплект ребрендинга»: он берёт проверенный open-source клиент,
меняет имя, иконку и цвет, и собирает готовый файл в GitHub Actions.
Тебе не нужны Android Studio, Mac или опыт программирования.

| Платформа | Донор | Что получится | Сложность |
|---|---|---|---|
| Android | [v2rayNG](https://github.com/2dust/v2rayNG) | `.apk`, ставится сразу | Легко |
| iOS | [SFI / sing-box](https://github.com/SagerNet/sing-box-for-apple) | `.ipa` без подписи | Сложно, нужен Apple ID |
| Windows | уже есть в `vpn/app` | `.exe` на Python + sing-box | Готово |

> **Важно про iPhone.** Apple разрешает VPN-приложения только через
> entitlement `Network Extension`, а его выдают **платным** аккаунтам
> разработчика (**99 $/год**). Бесплатный Apple ID для VPN-приложения,
> как правило, не подходит. Поэтому:
> * хочешь «своё» iOS-приложение → нужен платный Apple Developer;
> * не хочешь платить → ставь **Happ / Streisand / SFI** из App Store
>   и импортируй нашу ссылку. Функционально это то же самое.

---

## 0. Что нужно

1. Аккаунт **GitHub** (бесплатный): <https://github.com/signup>.
2. Ссылка `vless://...` с твоего сервера (см. `../SERVER-FROM-ZERO.md`).
3. 20–40 минут на первую сборку.

Всё остальное (Java, Android SDK, NDK, Gradle) GitHub поставит сам.

---

## 1. Загрузи этот комплект на GitHub

Нужен **свой репозиторий**, в котором лежат файлы из этой папки:
`brand.json`, `apply_brand.py`, `assets/`, `tools/`, `.github/workflows/`.

### Способ А. Через сайт GitHub (без установки программ)

1. GitHub → **New repository** → имя, например `flickvpn-app` → **Create**.
2. На странице репозитория: **Add file → Upload files**.
3. Перетащи **содержимое** папки `branding-kit` (не саму папку):
   `brand.json`, `apply_brand.py`, `assets`, `tools`.
4. **Важно:** папку `.github` сайт при перетаскивании может не принять.
   Создай файл вручную:
   * **Add file → Create new file**
   * Имя файла: `.github/workflows/build-android.yml`
   * Вставь содержимое одноимённого файла из этой папки.
   * **Commit changes**.
5. Аналогично добавь `.github/workflows/build-ios.yml` (если нужен iPhone).

### Способ Б. Через GitHub Desktop (удобнее)

1. Установи <https://desktop.github.com>.
2. **File → Add local repository** → выбери папку `branding-kit`.
3. **Publish repository** (сними галочку «Keep this code private», если хочешь
   бесплатные macOS-минуты для iOS-сборки).

---

## 2. Настрой бренд

Открой `brand.json` и поменяй:

```json
{
  "appName": "FLICK-VPN",
  "androidAppId": "com.flickvpn.app",
  "iosBundleId": "com.flickvpn.app",
  "accentColor": "#3B82F6",
  "backgroundColor": "#0B1220",
  "versionName": "1.0.0"
}
```

* `appName` — имя под иконкой на телефоне.
* `androidAppId` / `iosBundleId` — уникальный идентификатор. Если он совпадёт
  с другим приложением, установка не встанет. Меняй на своё:
  `com.твоёимя.vpn`.
* `accentColor` — цвет кнопок и переключателей.
* `backgroundColor` — фон иконки.

После правки `brand.json` иконки нужно перегенерировать. Это можно сделать
локально (нужен Python + Pillow) **или** просто оставить текущие.

```powershell
python -m pip install pillow
python tools\make_icon.py
```

---

## 3. Собери APK для Android

1. В репозитории открой вкладку **Actions**.
2. Слева выбери **Build branded Android APK**.
3. Справа **Run workflow → Run workflow**.
4. Подожди 20–40 минут (первый раз долго: качается SDK и NDK).
5. Зайди в завершённый запуск → внизу **Artifacts** → скачай `android-apk`.
6. Внутри архива будет `.apk` (универсальный и/или под конкретные ABI).

Установка на телефон:

1. Перекинь `.apk` на Android (кабель, Telegram «Избранное», облако).
2. Открой файл → разреши «Установка из неизвестных источников».
3. Запусти приложение → **+** → **Импорт из буфера** (вставь `vless://...`)
   или **QR-код**.
4. Нажми кнопку подключения → разреши VPN.

> Приложение подписано **сгенерированным ключом**, а не ключом Google Play.
> Для личного использования и раздачи друзьям этого достаточно. Для Play
> Store нужен свой keystore и аккаунт разработчика (25 $ разово).

---

## 4. Собери приложение для iPhone (сложный путь)

### 4.1. Что понадобится

* **Apple Developer Program** — 99 $/год. Без него entitlement
  `Network Extension` не выдадут, и VPN не запустится.
* Любой Mac **или** macOS-раннер GitHub Actions (он бесплатный для
  публичных репозиториев).
* Программа для установки `.ipa`: **Sideloadly** (Windows/Mac) или AltStore.

### 4.2. Сборка

1. **Actions → Build branded iOS app (experimental) → Run workflow**.
2. Через 40–90 минут скачай артефакт `ios-unsigned-ipa`.
3. Внутри — `FLICK-VPN-unsigned.ipa` **без подписи**. Просто так он не встанет.

### 4.3. Подпись и установка

1. Установи [Sideloadly](https://sideloadly.io/).
2. Подключи iPhone кабелем.
3. Перетащи `.ipa` в Sideloadly.
4. Введи Apple ID (тот, что привязан к платному аккаунту разработчика).
5. Нажми **Start**. Sideloadly подпишет приложение твоим сертификатом.
6. На iPhone: **Настройки → Основные → VPN и управление устройством** →
   доверься профилю разработчика.
7. Запусти приложение → импортируй `vless://` → подключись.

> Если сборка упала: upstream SFI меняется каждую неделю. Открой лог,
> найди первую ошибку — обычно достаточно поменять версию Xcode или тег
> `upstreamIosCoreTag` в `brand.json`. Это действительно «продвинутый» путь;
> для большинства людей проще поставить готовый клиент из App Store.

---

## 5. Что именно меняет скрипт

`apply_brand.py` — единственное место, где происходит «магия». Он **не трогает
логику VPN**, только оформление:

**Android (v2rayNG):**
* `applicationId` и `versionName` в `app/build.gradle.kts`;
* `app_name` во всех языках;
* акцентный цвет в `ui/compose/Theme.kt`;
* цвет фона и все PNG-иконки (`mipmap-*`).

**iOS (SFI):**
* `1024.png`, `1024-dark.png`, `1024-tinted.png` в `AppIcon.appiconset`;
* `AccentColor.colorset`;
* `CFBundleDisplayName` в `Info.plist`;
* Bundle ID передаётся при сборке через `BASE_PACKAGE_IDENTIFIER`.

Посмотреть, что изменится, можно и без сборки — скрипт работает локально:

```powershell
git clone --recursive --branch 2.3.15 https://github.com/2dust/v2rayNG.git upstream
python apply_brand.py --platform android --path upstream
```

---

## 6. Лицензии и честность

* v2rayNG — **GPLv3**, SFI — **GPLv3**. Если ты **раздаёшь** собранное
  приложение (друзьям, в чат, в стор), ты обязан выложить исходники
  (достаточно ссылки на форк) и сохранить уведомление об авторских правах.
  Для личного использования ничего публиковать не нужно.
* Нельзя использовать имена и логотипы upstream (v2rayNG, sing-box) —
  поэтому мы и меняем имя и иконку.
* Не продавай доступ и не обещай «анонимность»: VPN не делает тебя невидимым,
  а владелец сервера видит твой трафик.

---

## 7. Частые проблемы

| Проблема | Решение |
|---|---|
| Actions пишет `Resource not accessible` | Включи Actions: Settings → Actions → General → Allow all actions |
| `android-37.0` не найден | В workflow замени на `platforms;android-36 build-tools;36.0.0` и `compileSdk` в upstream |
| APK не устанавливается | Удали старое приложение с тем же `applicationId` |
| Приложение ставится, но VPN не включается | Проверь, что импортирован именно `vless://` с `security=reality` |
| iOS: «Unable to install» | `.ipa` не подписан или Apple ID без entitlement NE |
| iOS: сборка падает на `Libbox.xcframework` | Обнови `upstreamIosCoreTag` / версию Xcode |

---

## 8. Следующий шаг

1. Подними сервер: `../SERVER-FROM-ZERO.md`.
2. Получи `vless://`.
3. Собери APK (раздел 3) и поставь на Android.
4. На iPhone для начала поставь **Happ** из App Store — работает сразу.
5. Если нужен именно свой iOS-клиент — раздел 4.
