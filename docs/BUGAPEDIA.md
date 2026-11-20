# Bugapedia hosting and curator guide

The public home page lists every specimen in `specimens/catalog.json`. The sharable specimen route is `/explore/?specimen=SPECIES-ID`. Use **Share library** on the home page or **Share this specimen** below the viewer. Anyone with the public link can explore the models without an account.

## Preview from a fresh clone

Install Node 22.12 or newer, npm, and the Netlify CLI. From the repository root run:

```sh
npm ci
npm run build:site
npm run test:requests
```

Create a private local key if this is a fresh checkout. This command refuses to overwrite an existing configuration.

```sh
node --input-type=module -e 'import {writeFileSync} from "node:fs"; import {randomBytes} from "node:crypto"; writeFileSync(".env","BUGAPEDIA_OWNER_KEY="+randomBytes(36).toString("hex")+"\n",{flag:"wx",mode:0o600})'
netlify dev --offline --framework '#static' --dir dist --port 4191 --no-open
```

Open http://localhost:4191/. The offline CLI runs both functions and the local Blobs emulator. Open `/review/` and paste the value from your ignored `.env` file to see local submissions. Keep the key in your password manager. Local submissions live in ignored emulator storage. Rebuild the static site after editing it.

## Review an observation and build a model

1. A visitor opens **Suggest a bug**, selects a JPEG, PNG or WebP, optionally adds a tentative identification and a question, and grants permission for private review. A receipt confirms the photo reached the queue. Anyone helping a child can submit on their behalf.
2. On **Owner review**, enter the owner key. Open the private photo, check the identification, and enter the species ID and the educational feature to model. Choose **Approve for modeling** or **Decline request**. An approval records the curator's final decision. The photo and visitor's text stay private.
3. Download the approved private build request. In your local AnyBug checkout, run:

   ```sh
   python3 scripts/import-request.py ~/Downloads/bug-request-EXAMPLE.json
   ```

   Read the private brief and reference JPEG in `private/requests/REQUEST-ID/`. Imports can be retried. For an existing, authored species, `--rebuild` also runs its checked-in Blender pipeline. For a new species, follow [Add a species](ADDING-A-SPECIES.md) to research it, write the builder, register it, and run `python3 rebuild.py SPECIES-ID`. The visitor's observation is a starting point for identification. Internal anatomy and educational notes need independent references.
4. Verify the model, controls, labels and sources. Run `npm run build:site`, review the new library card and interactive model, then authorize the public release. Share the specimen page. Remove local download packets and private reference copies when you finish with them.

## Publish a reviewed version

Use a dedicated Netlify site. The checked-in configuration packages the two Node functions and serves only `dist/`. The build includes the catalog, viewer, model GLBs, anatomy manifests, and catalog illustrations. Editable Blender masters, private inputs and credentials stay outside the public bundle.

Set a new production-only secret named `BUGAPEDIA_OWNER_KEY` with Functions scope in the site's environment settings before deploying. Use a password manager to generate and retain a random key of at least 32 characters. Rotating the key requires a new deploy. Keep preview credentials separate. When the key is missing or too short, uploads and owner reads close automatically.

After approval, build and deploy from the reviewed commit with the Netlify CLI and the explicit site ID. Check the homepage and a direct specimen link in a signed-out session. Confirm the request endpoint accepts a synthetic image, anonymous access to the private queue is denied, and the curator can open the resulting request.

Production submissions persist in the site's strongly consistent `bugapedia-requests` Blobs store across deploys. Separate preview stores use deployment IDs. All photo, decision and build-packet reads require the owner key. Browser and server rebuild JPEGs from pixels to discard embedded metadata. Content visible in the image is preserved. The API accepts a bounded body and configures per-IP rate limits. No family photo, location metadata, contact list or owner key belongs in Git or the public site.

For a visitor deletion request, use the receipt suffix to locate the matching full ID in the site’s private Blobs store. Confirm the intended entry and remove its `photos/REQUEST-ID` and any `decisions/REQUEST-ID` entry, plus any downloaded private copies.
