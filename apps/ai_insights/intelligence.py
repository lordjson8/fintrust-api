from collections import Counter
from decimal import Decimal, InvalidOperation

from django.db.models import Avg, Count, Sum

from apps.credit_scoring.models import RiskProfile
from apps.fraud_detection.models import FraudAlert
from apps.transactions.models import Transaction


TEXT = {
    'en': {
        'credit_income_positive': 'Income level supports stronger repayment capacity.',
        'credit_income_negative': 'Low monthly income limits affordable loan size.',
        'credit_frequency_positive': 'Frequent mobile money activity provides strong behavioral history.',
        'credit_frequency_negative': 'Thin mobile money activity gives limited behavioral evidence.',
        'credit_late_positive': 'No recent late payments were reported.',
        'credit_late_many': 'Multiple late payments materially weaken the score.',
        'credit_late_some': 'Recent late payments reduce repayment confidence.',
        'credit_age_positive': 'Long account history improves confidence in the assessment.',
        'credit_age_negative': 'Short account age reduces scoring confidence.',
        'credit_positive_fallback': 'Profile has enough baseline data for a preliminary score.',
        'credit_negative_fallback': 'No major negative factor dominated this assessment.',
        'credit_next_approve': 'Eligible for standard approval with routine monitoring.',
        'credit_next_review': 'Review affordability and consider a smaller starter loan.',
        'credit_next_escalate': 'Escalate for manual review before approving credit.',
        'credit_what_if_late': 'Reduce late payments to improve repayment probability.',
        'credit_what_if_activity': 'Increase consistent mobile money activity for at least 60 days.',
        'credit_what_if_exposure': 'Keep loan exposure below the recommended amount for this cycle.',
        'fraud_amount_5x': 'Amount is at least five times the customer baseline.',
        'fraud_amount_2x': 'Amount is materially above the customer baseline.',
        'fraud_device': 'A new or changed device was reported.',
        'fraud_location': 'Transaction location captured as {location}.',
        'fraud_signal_fallback': 'No high-impact behavioral signal was isolated.',
        'fraud_next_block': 'Block or hold the transaction and require enhanced verification.',
        'fraud_next_review': 'Flag for analyst review before settlement.',
        'fraud_next_allow': 'Allow with passive monitoring.',
        'fraud_rule': 'Escalate future transactions with device change or amount above 2x baseline.',
        'timeline_transaction': '{type} transaction',
        'timeline_transaction_detail': '{amount} via {method} in {location}',
        'timeline_credit': 'Credit score generated',
        'timeline_credit_detail': 'Risk score {score}, recommended loan {loan}',
        'timeline_fraud': '{urgency} fraud alert',
        'timeline_fraud_detail': '{probability}% probability, action {action}',
        'tx_alert_high_value': '{count} transaction(s) are at least 3x the customer average.',
        'tx_alert_device': '{count} transaction(s) involved a device change.',
        'tx_alert_limited': 'Limited transaction history; use a conservative decision threshold.',
        'portfolio_fraud_title': 'Fraud queue requires attention',
        'portfolio_fraud_detail': '{review} active alert(s), including {blocked} block recommendation(s).',
        'portfolio_credit_title': 'High-risk credit segment',
        'portfolio_credit_detail': '{count} customer(s) have a risk score below 40.',
        'portfolio_empty_title': 'No transaction history yet',
        'portfolio_empty_detail': 'Import transactions to activate monitoring and behavioral scoring.',
        'segment_stable': 'Stable low-risk borrowers',
        'segment_stable_rec': 'Offer normal loan limits with routine monitoring.',
        'segment_watchlist': 'Watchlist customers',
        'segment_watchlist_rec': 'Use smaller loan limits and require recent transaction review.',
        'segment_high': 'High-risk customers',
        'segment_high_rec': 'Escalate to manual review before approval.',
        'portfolio_rec_fraud': 'Review blocked and high-urgency fraud alerts before new credit approvals.',
        'portfolio_rec_credit': 'Prioritize customers with stable mobile money activity for faster approval.',
        'portfolio_rec_quality': 'Require dataset quality review before relying on large batch uploads.',
        'quality_outlier': 'Amount is at least 5x the dataset average.',
        'quality_rec_invalid': 'Fix invalid rows before production scoring.',
        'quality_rec_duplicate': 'Remove duplicate records to avoid biased portfolio analytics.',
        'quality_rec_outlier': 'Investigate amount outliers before fraud or credit decisions.',
    },
    'fr': {
        'credit_income_positive': 'Le niveau de revenu renforce la capacité de remboursement.',
        'credit_income_negative': 'Un revenu mensuel faible limite le montant de prêt abordable.',
        'credit_frequency_positive': 'Une activité Mobile Money fréquente fournit un historique comportemental solide.',
        'credit_frequency_negative': "Une activité Mobile Money limitée donne peu d'éléments comportementaux.",
        'credit_late_positive': 'Aucun retard de paiement récent n’a été signalé.',
        'credit_late_many': 'Plusieurs retards de paiement affaiblissent fortement le score.',
        'credit_late_some': 'Les retards récents réduisent la confiance de remboursement.',
        'credit_age_positive': "Un historique de compte long améliore la confiance dans l'évaluation.",
        'credit_age_negative': "Une ancienneté de compte courte réduit la confiance du scoring.",
        'credit_positive_fallback': 'Le profil contient assez de données pour un score préliminaire.',
        'credit_negative_fallback': "Aucun facteur négatif majeur ne domine cette évaluation.",
        'credit_next_approve': 'Éligible à une approbation standard avec surveillance normale.',
        'credit_next_review': 'Vérifier l’abordabilité et envisager un prêt initial plus petit.',
        'credit_next_escalate': 'Escalader en revue manuelle avant toute approbation de crédit.',
        'credit_what_if_late': 'Réduire les retards de paiement pour améliorer la probabilité de remboursement.',
        'credit_what_if_activity': 'Augmenter une activité Mobile Money régulière pendant au moins 60 jours.',
        'credit_what_if_exposure': 'Garder l’exposition de prêt sous le montant recommandé pour ce cycle.',
        'fraud_amount_5x': 'Le montant est au moins cinq fois supérieur à la référence client.',
        'fraud_amount_2x': 'Le montant est nettement supérieur à la référence client.',
        'fraud_device': 'Un appareil nouveau ou modifié a été signalé.',
        'fraud_location': 'Localisation de transaction capturée : {location}.',
        'fraud_signal_fallback': 'Aucun signal comportemental à fort impact n’a été isolé.',
        'fraud_next_block': 'Bloquer ou retenir la transaction et exiger une vérification renforcée.',
        'fraud_next_review': 'Signaler pour revue analyste avant règlement.',
        'fraud_next_allow': 'Autoriser avec surveillance passive.',
        'fraud_rule': 'Escalader les prochaines transactions avec changement d’appareil ou montant supérieur à 2x la référence.',
        'timeline_transaction': 'Transaction {type}',
        'timeline_transaction_detail': '{amount} via {method} à {location}',
        'timeline_credit': 'Score crédit généré',
        'timeline_credit_detail': 'Score de risque {score}, prêt recommandé {loan}',
        'timeline_fraud': 'Alerte fraude {urgency}',
        'timeline_fraud_detail': '{probability}% de probabilité, action {action}',
        'tx_alert_high_value': '{count} transaction(s) atteignent au moins 3x la moyenne client.',
        'tx_alert_device': '{count} transaction(s) impliquent un changement d’appareil.',
        'tx_alert_limited': 'Historique transactionnel limité ; utiliser un seuil de décision conservateur.',
        'portfolio_fraud_title': 'La file fraude nécessite une attention',
        'portfolio_fraud_detail': '{review} alerte(s) active(s), dont {blocked} recommandation(s) de blocage.',
        'portfolio_credit_title': 'Segment crédit à haut risque',
        'portfolio_credit_detail': '{count} client(s) ont un score de risque inférieur à 40.',
        'portfolio_empty_title': 'Aucun historique de transaction',
        'portfolio_empty_detail': 'Importez des transactions pour activer la surveillance et le scoring comportemental.',
        'segment_stable': 'Emprunteurs stables à faible risque',
        'segment_stable_rec': 'Proposer des limites de prêt normales avec surveillance standard.',
        'segment_watchlist': 'Clients sous surveillance',
        'segment_watchlist_rec': 'Utiliser des limites plus petites et vérifier les transactions récentes.',
        'segment_high': 'Clients à haut risque',
        'segment_high_rec': 'Escalader en revue manuelle avant approbation.',
        'portfolio_rec_fraud': 'Examiner les alertes fraude bloquées et urgentes avant tout nouveau crédit.',
        'portfolio_rec_credit': 'Prioriser les clients avec une activité Mobile Money stable pour une approbation plus rapide.',
        'portfolio_rec_quality': 'Exiger un contrôle qualité des données avant les grands imports batch.',
        'quality_outlier': 'Le montant est au moins 5x supérieur à la moyenne du jeu de données.',
        'quality_rec_invalid': 'Corriger les lignes invalides avant le scoring en production.',
        'quality_rec_duplicate': 'Supprimer les doublons pour éviter de biaiser les analyses du portefeuille.',
        'quality_rec_outlier': 'Examiner les montants atypiques avant les décisions fraude ou crédit.',
    },
}


def _language(data=None):
    language = (data or {}).get('language', 'en')
    return 'fr' if str(language).lower().startswith('fr') else 'en'


def _t(language, key, **kwargs):
    return TEXT.get(language, TEXT['en'])[key].format(**kwargs)


def _to_decimal(value, default='0'):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _money(value):
    return int(_to_decimal(value))


def _risk_band(score):
    if score < 40:
        return 'high_risk'
    if score < 70:
        return 'watchlist'
    return 'low_risk'


def build_credit_explainability(data, ai_result):
    language = _language(data)
    score = int(ai_result.get('risk_score') or 0)
    income = int(data.get('monthly_income') or 0)
    frequency = int(data.get('mobile_money_frequency') or 0)
    late_payments = int(data.get('late_payments') or 0)
    account_age = int(data.get('account_age_months') or 0)

    positive = []
    negative = []

    if income >= 250000:
        positive.append(_t(language, 'credit_income_positive'))
    elif income < 75000:
        negative.append(_t(language, 'credit_income_negative'))

    if frequency >= 20:
        positive.append(_t(language, 'credit_frequency_positive'))
    elif frequency < 5:
        negative.append(_t(language, 'credit_frequency_negative'))

    if late_payments == 0:
        positive.append(_t(language, 'credit_late_positive'))
    elif late_payments >= 3:
        negative.append(_t(language, 'credit_late_many'))
    else:
        negative.append(_t(language, 'credit_late_some'))

    if account_age >= 24:
        positive.append(_t(language, 'credit_age_positive'))
    elif account_age < 6:
        negative.append(_t(language, 'credit_age_negative'))

    if not positive:
        positive.append(_t(language, 'credit_positive_fallback'))
    if not negative:
        negative.append(_t(language, 'credit_negative_fallback'))

    if score >= 75:
        next_action = _t(language, 'credit_next_approve')
    elif score >= 50:
        next_action = _t(language, 'credit_next_review')
    else:
        next_action = _t(language, 'credit_next_escalate')

    confidence = 'high'
    if account_age < 6 or frequency < 5:
        confidence = 'low'
    elif account_age < 12 or frequency < 12:
        confidence = 'medium'

    return {
        'risk_band': _risk_band(score),
        'confidence': confidence,
        'positive_factors': positive[:4],
        'negative_factors': negative[:4],
        'next_action': next_action,
        'what_if': [
            _t(language, 'credit_what_if_late'),
            _t(language, 'credit_what_if_activity'),
            _t(language, 'credit_what_if_exposure'),
        ],
    }


def build_fraud_explainability(data, ai_result):
    language = _language(data)
    probability = int(ai_result.get('fraud_probability') or 0)
    amount = _to_decimal(data.get('amount'))
    avg_amount = _to_decimal(data.get('avg_amount'), default='150000')
    device_change = bool(data.get('device_change'))
    location = data.get('location') or 'Unknown'

    signals = []
    if avg_amount > 0 and amount >= avg_amount * 5:
        signals.append(_t(language, 'fraud_amount_5x'))
    elif avg_amount > 0 and amount >= avg_amount * 2:
        signals.append(_t(language, 'fraud_amount_2x'))

    if device_change:
        signals.append(_t(language, 'fraud_device'))
    if location:
        signals.append(_t(language, 'fraud_location', location=location))
    if not signals:
        signals.append(_t(language, 'fraud_signal_fallback'))

    if probability >= 80:
        next_action = _t(language, 'fraud_next_block')
    elif probability >= 50:
        next_action = _t(language, 'fraud_next_review')
    else:
        next_action = _t(language, 'fraud_next_allow')

    confidence = 'high' if avg_amount > 0 and data.get('transaction_id') else 'medium'

    return {
        'confidence': confidence,
        'signals': signals[:5],
        'next_action': next_action,
        'monitoring_rule': _t(language, 'fraud_rule'),
    }


def build_transaction_insights(transactions, language='en'):
    language = _language({'language': language})
    rows = list(transactions)
    if not rows:
        return {
            'transaction_count': 0,
            'total_volume': 0,
            'average_amount': 0,
            'volatility': 'unknown',
            'dominant_method': None,
            'dominant_location': None,
            'alerts': [],
        }

    amounts = [_to_decimal(tx.amount) for tx in rows]
    total = sum(amounts, Decimal('0'))
    average = total / len(amounts)
    max_amount = max(amounts)
    method = Counter(tx.payment_method for tx in rows if tx.payment_method).most_common(1)
    location = Counter(tx.location for tx in rows if tx.location).most_common(1)
    device_changes = sum(1 for tx in rows if tx.device_change)
    high_value_count = sum(1 for amount in amounts if average > 0 and amount >= average * 3)

    alerts = []
    if high_value_count:
        alerts.append(_t(language, 'tx_alert_high_value', count=high_value_count))
    if device_changes:
        alerts.append(_t(language, 'tx_alert_device', count=device_changes))
    if len(rows) < 5:
        alerts.append(_t(language, 'tx_alert_limited'))

    volatility = 'low'
    if average > 0 and max_amount >= average * 5:
        volatility = 'high'
    elif average > 0 and max_amount >= average * 2:
        volatility = 'medium'

    return {
        'transaction_count': len(rows),
        'total_volume': _money(total),
        'average_amount': _money(average),
        'volatility': volatility,
        'dominant_method': method[0][0] if method else None,
        'dominant_location': location[0][0] if location else None,
        'alerts': alerts,
    }


def build_customer_timeline(user, limit=30, language='en'):
    language = _language({'language': language})
    events = []

    for tx in Transaction.objects.filter(user=user).order_by('-timestamp')[:limit]:
        events.append({
            'type': 'transaction',
            'timestamp': tx.timestamp,
            'title': _t(language, 'timeline_transaction', type=tx.type.title()),
            'description': _t(
                language,
                'timeline_transaction_detail',
                amount=_money(tx.amount),
                method=tx.payment_method,
                location=tx.location,
            ),
            'severity': 'warning' if tx.device_change else 'info',
            'object_id': str(tx.id),
        })

    for profile in RiskProfile.objects.filter(user=user).order_by('-created_at')[:limit]:
        events.append({
            'type': 'credit_score',
            'timestamp': profile.created_at,
            'title': _t(language, 'timeline_credit'),
            'description': _t(
                language,
                'timeline_credit_detail',
                score=profile.risk_score,
                loan=_money(profile.recommended_loan),
            ),
            'severity': 'critical' if profile.risk_score < 40 else 'success',
            'object_id': str(profile.id),
        })

    alerts = FraudAlert.objects.filter(transaction__user=user).select_related('transaction').order_by('-created_at')[:limit]
    for alert in alerts:
        events.append({
            'type': 'fraud_alert',
            'timestamp': alert.created_at,
            'title': _t(language, 'timeline_fraud', urgency=alert.urgency.title()),
            'description': _t(
                language,
                'timeline_fraud_detail',
                probability=alert.fraud_probability,
                action=alert.action,
            ),
            'severity': 'critical' if alert.action == 'BLOCK' else 'warning',
            'object_id': str(alert.id),
        })

    events.sort(key=lambda item: item['timestamp'], reverse=True)
    return events[:limit]


def build_portfolio_intelligence(transactions, risk_profiles, fraud_alerts, language='en'):
    language = _language({'language': language})
    total_transactions = transactions.count()
    total_volume = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    avg_amount = transactions.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
    blocked_alerts = fraud_alerts.filter(action='BLOCK').count()
    review_alerts = fraud_alerts.exclude(action='ALLOW').count()
    high_risk_customers = risk_profiles.filter(risk_score__lt=40).values('user').distinct().count()

    monitoring_alerts = []
    if review_alerts:
        monitoring_alerts.append({
            'level': 'high' if blocked_alerts else 'medium',
            'title': _t(language, 'portfolio_fraud_title'),
            'detail': _t(language, 'portfolio_fraud_detail', review=review_alerts, blocked=blocked_alerts),
        })
    if high_risk_customers:
        monitoring_alerts.append({
            'level': 'medium',
            'title': _t(language, 'portfolio_credit_title'),
            'detail': _t(language, 'portfolio_credit_detail', count=high_risk_customers),
        })
    if total_transactions == 0:
        monitoring_alerts.append({
            'level': 'low',
            'title': _t(language, 'portfolio_empty_title'),
            'detail': _t(language, 'portfolio_empty_detail'),
        })

    segments = [
        {
            'key': 'stable_low_risk',
            'label': _t(language, 'segment_stable'),
            'count': risk_profiles.filter(risk_score__gte=70).values('user').distinct().count(),
            'recommendation': _t(language, 'segment_stable_rec'),
        },
        {
            'key': 'watchlist',
            'label': _t(language, 'segment_watchlist'),
            'count': risk_profiles.filter(risk_score__gte=40, risk_score__lt=70).values('user').distinct().count(),
            'recommendation': _t(language, 'segment_watchlist_rec'),
        },
        {
            'key': 'high_risk',
            'label': _t(language, 'segment_high'),
            'count': high_risk_customers,
            'recommendation': _t(language, 'segment_high_rec'),
        },
    ]

    return {
        'total_volume': _money(total_volume),
        'average_transaction_amount': _money(avg_amount),
        'monitoring_alerts': monitoring_alerts,
        'segments': segments,
        'recommendations': [
            _t(language, 'portfolio_rec_fraud'),
            _t(language, 'portfolio_rec_credit'),
            _t(language, 'portfolio_rec_quality'),
        ],
    }


def build_dataset_quality_report(entries, serializer_class, required_fields, language='en'):
    language = _language({'language': language})
    total = len(entries)
    duplicate_rows = 0
    seen = set()
    field_missing = Counter()
    invalid_rows = []
    amount_values = []

    for index, entry in enumerate(entries, start=1):
        row_key = tuple(sorted((str(k), str(v)) for k, v in entry.items()))
        if row_key in seen:
            duplicate_rows += 1
        seen.add(row_key)

        for field in required_fields:
            if entry.get(field) in (None, ''):
                field_missing[field] += 1

        serializer = serializer_class(data=entry)
        if not serializer.is_valid():
            invalid_rows.append({
                'row': index,
                'errors': serializer.errors,
            })

        if 'amount' in entry:
            amount_values.append(_to_decimal(entry.get('amount')))

    outlier_rows = []
    if amount_values:
        avg = sum(amount_values, Decimal('0')) / len(amount_values)
        for index, entry in enumerate(entries, start=1):
            amount = _to_decimal(entry.get('amount'))
            if avg > 0 and amount >= avg * 5:
                outlier_rows.append({
                    'row': index,
                    'field': 'amount',
                    'message': _t(language, 'quality_outlier'),
                })

    issue_count = len(invalid_rows) + duplicate_rows + sum(field_missing.values()) + len(outlier_rows)
    score = 100 if total else 0
    if total:
        score = max(0, round(100 - min(100, (issue_count / total) * 20)))

    return {
        'total_rows': total,
        'valid_rows': max(0, total - len(invalid_rows)),
        'invalid_rows': len(invalid_rows),
        'duplicate_rows': duplicate_rows,
        'quality_score': score,
        'missing_fields': dict(field_missing),
        'outliers': outlier_rows[:25],
        'row_errors': invalid_rows[:50],
        'recommendations': [
            _t(language, 'quality_rec_invalid'),
            _t(language, 'quality_rec_duplicate'),
            _t(language, 'quality_rec_outlier'),
        ],
    }
