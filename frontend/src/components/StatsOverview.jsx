import React from 'react';
import { LayoutGrid, CheckCircle2, Building, Shield } from 'lucide-react';

export default function StatsOverview({ apps = [], user }) {
  const activeCount = apps.filter((a) => a.activo).length;
  const userDept = user?.profile?.department || 'No Asignado';
  const adGroupsCount = user?.profile?.ad_groups?.length || 0;

  return (
    <div className="stats-grid" id="stats-overview-grid">
      <div className="stat-card-glass" id="stat-total-apps">
        <div className="stat-icon-box stat-icon-blue">
          <LayoutGrid size={24} />
        </div>
        <div>
          <div className="stat-value" id="stat-val-total">{apps.length}</div>
          <div className="stat-title">Aplicativos Autorizados</div>
        </div>
      </div>

      <div className="stat-card-glass" id="stat-active-apps">
        <div className="stat-icon-box stat-icon-green">
          <CheckCircle2 size={24} />
        </div>
        <div>
          <div className="stat-value" id="stat-val-active">{activeCount}</div>
          <div className="stat-title">Enlaces Habilitados</div>
        </div>
      </div>

      <div className="stat-card-glass" id="stat-user-dept">
        <div className="stat-icon-box stat-icon-cyan">
          <Building size={24} />
        </div>
        <div>
          <div className="stat-value" style={{ fontSize: '1.15rem' }} id="stat-val-dept">
            {userDept}
          </div>
          <div className="stat-title">Departamento AD</div>
        </div>
      </div>

      <div className="stat-card-glass" id="stat-ad-groups">
        <div className="stat-icon-box stat-icon-purple">
          <Shield size={24} />
        </div>
        <div>
          <div className="stat-value" id="stat-val-groups">{adGroupsCount}</div>
          <div className="stat-title">Grupos AD Sincronizados</div>
        </div>
      </div>
    </div>
  );
}
