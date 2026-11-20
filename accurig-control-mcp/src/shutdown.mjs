export async function stopOwnedApplication({requestQuit,disconnect,isRunning,forceTerminate,sleep=ms=>new Promise(r=>setTimeout(r,ms)),now=Date.now,timeoutMs=15000}){
 await requestQuit();
 // Electron/Node can wait for its inspector to detach before process exit.
 // Waiting on the PID while keeping CDP connected creates a shutdown deadlock.
 disconnect();
 let deadline=now()+timeoutMs,forced=false;
 while(await isRunning()){
  if(now()>=deadline){if(forced||!forceTerminate)throw Error('APPLICATION_EXIT_NOT_CONFIRMED');await forceTerminate();forced=true;deadline=now()+timeoutMs;}
  await sleep(100);
 }
 return {exit_verified:true,forced_owned_process_exit:forced};
}
