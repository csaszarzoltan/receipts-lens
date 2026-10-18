"use client";
import {useEffect, useRef} from 'react';

/** Shared modal keyboard behavior, including focus return and background isolation. */
export function useDialogFocus(open: boolean, onClose: () => void) {
  const ref=useRef<HTMLDivElement>(null);
  const close=useRef(onClose); close.current=onClose;
  useEffect(()=>{
    const dialog=ref.current;
    if(!open || !dialog) return;
    const previous=document.activeElement as HTMLElement | null;
    const oldOverflow=document.body.style.overflow;
    document.body.style.overflow='hidden';
    const inerted:HTMLElement[]=[];
    let ancestor:HTMLElement=dialog;
    while(ancestor.parentElement) {
      for(const sibling of Array.from(ancestor.parentElement.children)) {
        if(sibling!==ancestor && sibling instanceof HTMLElement && !sibling.inert && !['SCRIPT','STYLE'].includes(sibling.tagName)) {sibling.inert=true;inerted.push(sibling);}
      }
      ancestor=ancestor.parentElement;
      if(ancestor===document.body) break;
    }
    const focusable=()=>Array.from(dialog.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex="0"]')).filter(el=>!el.hidden && el.getClientRects().length>0 && !el.closest('[inert]'));
    (focusable()[0] ?? dialog).focus();
    const key=(event:KeyboardEvent)=>{
      if(event.key==='Escape') {event.preventDefault();close.current();}
      if(event.key!=='Tab') return;
      const nodes=focusable(),first=nodes[0],last=nodes.at(-1);
      if(!first) {event.preventDefault();dialog.focus();return;}
      if(event.shiftKey && (document.activeElement===first || document.activeElement===dialog)) {event.preventDefault();last?.focus();}
      else if(!event.shiftKey && (document.activeElement===last || !dialog.contains(document.activeElement))) {event.preventDefault();first.focus();}
    };
    const focus=(event:FocusEvent)=>{if(!dialog.contains(event.target as Node)) (focusable()[0] ?? dialog).focus();};
    document.addEventListener('keydown',key);document.addEventListener('focusin',focus);
    return()=>{document.removeEventListener('keydown',key);document.removeEventListener('focusin',focus);document.body.style.overflow=oldOverflow;for(const node of inerted)node.inert=false;if(previous?.isConnected)previous.focus();};
  },[open]);
  return ref;
}
