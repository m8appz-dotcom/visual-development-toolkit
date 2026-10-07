import socket,subprocess,pathlib,json
root=pathlib.Path(__file__).parent
domains=['deb.debian.org','security.debian.org','pypi.org','files.pythonhosted.org','registry.npmjs.org']
hosts={host:socket.gethostbyname(host) for host in domains}
(root/'reports'/'build-network.json').write_text(json.dumps(hosts,indent=2))
argv=['docker','build','-t','modding-lab:1.0.0','--progress','plain']
for host,ip in hosts.items():argv+=['--add-host',f'{host}:{ip}']
argv+=['.']
with (root/'logs'/'docker-build.log').open('w') as log:
    subprocess.run(argv,cwd=root,stdout=log,stderr=log,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
with (root/'logs'/'docker-fix-build.log').open('w') as log:
    subprocess.run(['docker','build','-f','Dockerfile.fix','-t','modding-lab:1.0.2','.'],cwd=root,stdout=log,stderr=log,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
