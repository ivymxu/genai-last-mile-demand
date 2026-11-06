# Create and publish the repository

The connected GitHub profile is ivymxu. The connector available in this session can inspect and edit files but cannot create repositories. Local GitHub CLI authentication failed because its saved token is invalid. No remote repository was created or pushed.

The local repository includes an initial commit. From its directory, authenticate and create a private repository:

```sh
gh auth login --hostname github.com
gh repo create ivymxu/genai-last-mile-demand --private --source=. --remote=origin --push
```

Use a different name if it is already taken. Private visibility is a conservative starting point for coursework. Invite teammates through GitHub Settings → Collaborators. Select a license with your team before making the repository public.

If using the browser, create an empty private repository named genai-last-mile-demand under ivymxu. Do not initialize it with a README, license or gitignore. Then run:

```sh
git remote add origin https://github.com/ivymxu/genai-last-mile-demand.git
git push -u origin main
```

Confirm that the Actions test workflow passes. Generated future experiment folders named artifacts are ignored; the default example is committed deliberately. No credentials or original course document are included.
