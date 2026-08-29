export default function NextAction({ action }: { action: string }) {
  return (
    <section className="panel panel--next-action">
      <h2>Prossima azione globale</h2>
      <div className="next-action">{action}</div>
    </section>
  );
}
